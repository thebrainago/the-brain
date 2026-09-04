//+------------------------------------------------------------------+
//|                    Hybrid_Microstructure_EA_V1.0.mq5             |
//|                                                                  |
//| Core Engine : Tick VWAP + Deviation Band + Velocity Sweep        |
//|               + Snapback + MTF Trend + M5 Setup + M1 Structure   |
//|                                                                  |
//| Architecture:                                                    |
//| H1 -> M15 -> M5 -> M1 -> Execution                               |
//|                                                                  |
//| Designed for: XAUUSD Scalping / Intraday Microstructure          |
//+------------------------------------------------------------------+
#property copyright "Copyright©2023. Ritz EAneha©"
#property link      "https://www.mql5.com/en/users/ritzfalih"
#property version   "1.0"
#property description "Core Engine :\nTick VWAP + Deviation Band + Velocity Sweep\n+ Snapback + MTF Trend + M5 Setup + M1 Structure"
#property description "Architecture:\nH1 -> M15 -> M5 -> M1 -> Execution\nDesigned for: XAUUSD Scalping / Intraday Microstructure"
#property strict

//+------------------------------------------------------------------+
//| AI BRIDGE & DECISION INTELLIGENCE                                |
//+------------------------------------------------------------------+
#include <HybridMicrostructure\ParamUX.mqh>
#include <HybridMicrostructure\AIBridge.mqh>
#include <HybridMicrostructure\AIBridgeUX.mqh>

//+------------------------------------------------------------------+
//| DATA STRUCTURE                                                    |
//+------------------------------------------------------------------+
struct TickData
{
    double         bid;
    double         ask;
    ulong          volume;
    long           time_msc;
};

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+
TickData tick_buffer[];

int  buffer_index  = 0;
bool buffer_filled = false;

double pips_multiplier = 1.0;

// Indicator handles
int handle_atr_m1 = INVALID_HANDLE;

int handle_ma_h1  = INVALID_HANDLE;
int handle_ma_m15 = INVALID_HANDLE;
int handle_ma_m5  = INVALID_HANDLE;

// Trading state
bool   is_sweeping_up   = false;
bool   is_sweeping_down = false;

double extreme_peak = 0.0;

// Last entry information
datetime last_entry_time = 0;
double   last_entry_price = 0.0;

// Bar tracking
datetime last_entry_bar_m5 = 0;

//+------------------------------------------------------------------+
//| EXPERT INITIALIZATION                                            |
//+------------------------------------------------------------------+
int OnInit()
{
    // Validate tick buffer
    if (InpTickBufferSize < 50)
    {
        Print("[INIT ERROR] InpTickBufferSize must be >= 50");
        return (INIT_PARAMETERS_INCORRECT);
    }

    ArrayResize(tick_buffer, InpTickBufferSize);

    // Pip conversion
    int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

    pips_multiplier = (digits == 3 || digits == 5) ? 10.0 : 1.0;

    // M1 ATR
    if (InpUseM1Filter || InpSLTPMode == SLTP_ATR)
    {
        handle_atr_m1 = iATR(_Symbol, PERIOD_M1, InpM1ATRPeriod);

        if (handle_atr_m1 == INVALID_HANDLE)
        {
            Print("[INIT ERROR] Failed to create M1 ATR handle");
            return (INIT_FAILED);
        }
    }

    // H1 MA
    if (InpUseTrendFilter && InpUseH1Trend)
    {
        handle_ma_h1 = iMA(
            _Symbol,
            PERIOD_H1,
            InpH1MAPeriod,
            0,
            InpMAMethod,
            PRICE_CLOSE
        );

        if (handle_ma_h1 == INVALID_HANDLE)
        {
            Print("[INIT ERROR] Failed to create H1 MA handle");
            return (INIT_FAILED);
        }
    }

    // M15 MA
    if (InpUseTrendFilter && InpUseM15Trend)
    {
        handle_ma_m15 = iMA(
            _Symbol,
            PERIOD_M15,
            InpM15MAPeriod,
            0,
            InpMAMethod,
            PRICE_CLOSE
        );

        if (handle_ma_m15 == INVALID_HANDLE)
        {
            Print("[INIT ERROR] Failed to create M15 MA handle");
            return (INIT_FAILED);
        }
    }

    // M5 MA
    if (InpUseTrendFilter && InpUseM5Trend)
    {
        handle_ma_m5 = iMA(
            _Symbol,
            PERIOD_M5,
            InpM5MAPeriod,
            0,
            InpMAMethod,
            PRICE_CLOSE
        );

        if (handle_ma_m5 == INVALID_HANDLE)
        {
            Print("[INIT ERROR] Failed to create M5 MA handle");
            return (INIT_FAILED);
        }
    }

    // Reset states
    ResetSweepState();

    last_entry_time   = 0;
    last_entry_price  = 0;
    last_entry_bar_m5 = 0;

    Print("--------------------------------------------------");
    AIBridge_Init();

    Print(" Hybrid Microstructure EA V1.0 INITIALIZED");
    Print(" Symbol: ", _Symbol);
    Print(" Pip multiplier: ", DoubleToString(pips_multiplier, 1));
    Print(" MTF Trend: H1 / M15 / M5");
    Print(" M1 Structure: CLOSED CANDLE");
    Print("--------------------------------------------------");

    return (INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| EXPERT DEINITIALIZATION                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    if (handle_atr_m1 != INVALID_HANDLE)
        IndicatorRelease(handle_atr_m1);

    if (handle_ma_h1 != INVALID_HANDLE)
        IndicatorRelease(handle_ma_h1);

    if (handle_ma_m15 != INVALID_HANDLE)
        IndicatorRelease(handle_ma_m15);

    if (handle_ma_m5 != INVALID_HANDLE)
        IndicatorRelease(handle_ma_m5);

    // AI Bridge cleanup (panel objects)
    AIBridge_Deinit();
}

//+------------------------------------------------------------------+
//| MAIN TICK                                                         |
//+------------------------------------------------------------------+
void OnTick()
{
    MqlTick current_tick;

    if (!SymbolInfoTick(_Symbol, current_tick))
        return;

    // Always manage existing positions first
    SecureProfits();

    // AI Bridge UX maintenance (panel refresh, outcome tracking, auto-tune)
    AIBridge_TickMaintenance();

    // Trading session
    if (!IsTradingSessionActive(current_tick.time))
    {
        ResetSweepState();
        return;
    }

    // Spread protection
    if (!IsSpreadAcceptable(current_tick))
        return;

    // Update tick buffer
    UpdateTickBuffer(current_tick);

    if (!buffer_filled)
        return;

    // M1 volatility filter
    if (!CheckM1Volatility())
        return;

    // Calculate tick VWAP
    double vwap    = 0.0;
    double std_dev = 0.0;

    CalculateTickVWAP(vwap, std_dev);

    if (std_dev <= 0.0)
        return;

    double upper_band = vwap + (std_dev * InpDevMultiplier);
    double lower_band = vwap - (std_dev * InpDevMultiplier);

    // Tick velocity
    bool is_high_velocity = IsHighVelocity(current_tick);

    // Position protection
    if (CountOpenPositions() >= InpMaxTotalPositions)
    {
        ResetSweepState();
        return;
    }

    // Directional sweep engine
    ProcessSweepLogic(
        current_tick,
        vwap,
        upper_band,
        lower_band,
        std_dev,
        is_high_velocity
    );
}

//+------------------------------------------------------------------+
//| UPDATE TICK BUFFER                                                |
//+------------------------------------------------------------------+
void UpdateTickBuffer(const MqlTick &tick)
{
    tick_buffer[buffer_index].bid = tick.bid;
    tick_buffer[buffer_index].ask = tick.ask;
    tick_buffer[buffer_index].volume = (tick.volume > 0) ? tick.volume : 1;
    tick_buffer[buffer_index].time_msc = tick.time_msc;

    buffer_index++;

    if (buffer_index >= InpTickBufferSize)
    {
        buffer_index = 0;
        buffer_filled = true;
    }
}

//+------------------------------------------------------------------+
//| HIGH VELOCITY DETECTION                                           |
//+------------------------------------------------------------------+
bool IsHighVelocity(const MqlTick &current_tick)
{
    int window_size = 10;

    if (window_size >= InpTickBufferSize)
        window_size = InpTickBufferSize - 1;

    int past_idx = buffer_index - window_size;

    if (past_idx < 0)
        past_idx += InpTickBufferSize;

    long delta_ms = current_tick.time_msc - tick_buffer[past_idx].time_msc;

    return (delta_ms > 0 && delta_ms < (long)InpVelocityWindowMs);
}

//+------------------------------------------------------------------+
//| PROCESS SWEEP LOGIC                                               |
//+------------------------------------------------------------------+
void ProcessSweepLogic(
    const MqlTick &tick,
    double vwap,
    double upper_band,
    double lower_band,
    double std_dev,
    bool is_high_velocity)
{
    //===============================================================
    // UPPER SWEEP -> POTENTIAL SELL
    //===============================================================
    if (tick.bid > upper_band && is_high_velocity)
    {
        is_sweeping_up   = true;
        is_sweeping_down = false;

        if (extreme_peak == 0.0 || tick.bid > extreme_peak)
        {
            extreme_peak = tick.bid;
        }
    }

    //===============================================================
    // HANDLE ACTIVE UPPER SWEEP
    //===============================================================
    if (is_sweeping_up)
    {
        double snapback_distance = InpSnapbackPips * _Point * pips_multiplier;
        double extra_move = InpRequireExtraMove ? InpExtraMovePips * _Point * pips_multiplier : 0.0;

        double snapback_level      = extreme_peak - snapback_distance;
        double confirmation_level  = snapback_level - extra_move;

        // SELL trigger
        if (tick.bid <= confirmation_level)
        {
            bool valid = true;

            if (!CanOpenNewTrade(ORDER_TYPE_SELL, tick.bid))
                valid = false;

            if (valid && !IsTrendAligned(ORDER_TYPE_SELL))
                valid = false;

            if (valid && !IsM5SetupValid(ORDER_TYPE_SELL))
                valid = false;

            if (valid && !ConfirmM1Structure(ORDER_TYPE_SELL))
                valid = false;

            // AI Bridge final gate
            if (valid)
            {
                valid = AIBridge_Confirm(
                    ORDER_TYPE_SELL,
                    tick.bid,
                    tick,
                    is_high_velocity,
                    vwap,
                    upper_band,
                    lower_band,
                    std_dev,
                    extreme_peak,
                    handle_atr_m1,
                    handle_ma_h1,
                    handle_ma_m15,
                    handle_ma_m5
                );
            }
                // AI gate verdict is the final authority

            if (valid)
            {
                ExecuteTrade(
                    ORDER_TYPE_SELL,
                    tick.bid,
                    vwap
                );
            }

            ResetSweepState();
        }
        else if (tick.bid < upper_band)
        {
            // Price returned inside the band without proper snapback
            ResetSweepState();
        }
    }

    //===============================================================
    // LOWER SWEEP -> POTENTIAL BUY
    //===============================================================
    if (tick.ask < lower_band && is_high_velocity)
    {
        is_sweeping_down = true;
        is_sweeping_up   = false;

        if (extreme_peak == 0.0 || tick.ask < extreme_peak)
        {
            extreme_peak = tick.ask;
        }
    }

    //===============================================================
    // HANDLE ACTIVE LOWER SWEEP
    //===============================================================
    if (is_sweeping_down)
    {
        double snapback_distance = InpSnapbackPips * _Point * pips_multiplier;
        double extra_move = InpRequireExtraMove ? InpExtraMovePips * _Point * pips_multiplier : 0.0;

        double snapback_level      = extreme_peak + snapback_distance;
        double confirmation_level  = snapback_level + extra_move;

        // BUY trigger
        if (tick.ask >= confirmation_level)
        {
            bool valid = true;

            if (!CanOpenNewTrade(ORDER_TYPE_BUY, tick.ask))
                valid = false;

            if (valid && !IsTrendAligned(ORDER_TYPE_BUY))
                valid = false;

            if (valid && !IsM5SetupValid(ORDER_TYPE_BUY))
                valid = false;

            if (valid && !ConfirmM1Structure(ORDER_TYPE_BUY))
                valid = false;

            // AI Bridge final gate
            if (valid)
            {
                valid = AIBridge_Confirm(
                    ORDER_TYPE_BUY,
                    tick.ask,
                    tick,
                    is_high_velocity,
                    vwap,
                    upper_band,
                    lower_band,
                    std_dev,
                    extreme_peak,
                    handle_atr_m1,
                    handle_ma_h1,
                    handle_ma_m15,
                    handle_ma_m5
                );
            }
                // AI gate verdict is final (BUY)

            if (valid)
            {
                ExecuteTrade(
                    ORDER_TYPE_BUY,
                    tick.ask,
                    vwap
                );
            }

            ResetSweepState();
        }
        else if (tick.ask > lower_band)
        {
            ResetSweepState();
        }
    }
}

//+------------------------------------------------------------------+
//| RESET SWEEP STATE                                                 |
//+------------------------------------------------------------------+
void ResetSweepState()
{
    is_sweeping_up   = false;
    is_sweeping_down = false;
    extreme_peak     = 0.0;
}

//+------------------------------------------------------------------+
//| M1 VOLATILITY FILTER                                              |
//+------------------------------------------------------------------+
bool CheckM1Volatility()
{
    if (!InpUseM1Filter)
        return (true);

    if (handle_atr_m1 == INVALID_HANDLE)
        return (false);

    double atr[1];

    if (CopyBuffer(handle_atr_m1, 0, 1, 1, atr) <= 0)
        return (false);

    double atr_pips = atr[0] / (_Point * pips_multiplier);

    if (atr_pips < InpMinM1ATRPips)
        return (false);

    if (InpMaxM1ATRPips > 0.0 && atr_pips > InpMaxM1ATRPips)
        return (false);

    return (true);
}

//+------------------------------------------------------------------+
//| MTF TREND ALIGNMENT                                               |
//+------------------------------------------------------------------+
bool IsTrendAligned(ENUM_ORDER_TYPE order_type)
{
    if (!InpUseTrendFilter)
        return (true);

    bool bullish = true;
    bool bearish = true;

    // H1
    if (InpUseH1Trend)
    {
        bool up   = false;
        bool down = false;

        if (!GetTFTrend(PERIOD_H1, handle_ma_h1, up, down))
            return (false);

        bullish &= up;
        bearish &= down;
    }

    // M15
    if (InpUseM15Trend)
    {
        bool up   = false;
        bool down = false;

        if (!GetTFTrend(PERIOD_M15, handle_ma_m15, up, down))
            return (false);

        bullish &= up;
        bearish &= down;
    }

    // M5
    if (InpUseM5Trend)
    {
        bool up   = false;
        bool down = false;

        if (!GetTFTrend(PERIOD_M5, handle_ma_m5, up, down))
            return (false);

        bullish &= up;
        bearish &= down;
    }

    if (order_type == ORDER_TYPE_BUY)
        return (bullish);

    if (order_type == ORDER_TYPE_SELL)
        return (bearish);

    return (false);
}

//+------------------------------------------------------------------+
//| GET TIMEFRAME TREND                                               |
//+------------------------------------------------------------------+
bool GetTFTrend(
    ENUM_TIMEFRAMES timeframe,
    int ma_handle,
    bool &trend_up,
    bool &trend_down)
{
    trend_up   = false;
    trend_down = false;

    if (ma_handle == INVALID_HANDLE)
        return (false);

    double ma[1];

    // Closed candle
    if (CopyBuffer(ma_handle, 0, 1, 1, ma) <= 0)
        return (false);

    MqlRates rates[1];

    if (CopyRates(_Symbol, timeframe, 1, 1, rates) <= 0)
        return (false);

    double close_price = rates[0].close;

    trend_up   = (close_price > ma[0]);
    trend_down = (close_price < ma[0]);

    return (true);
}

//+------------------------------------------------------------------+
//| M5 SETUP FILTER                                                   |
//+------------------------------------------------------------------+
bool IsM5SetupValid(ENUM_ORDER_TYPE order_type)
{
    if (!InpUseM5Setup)
        return (true);

    MqlRates rates[1];

    if (CopyRates(_Symbol, PERIOD_M5, 1, 1, rates) <= 0)
        return (false);

    if (!InpRequireM5CandleBias)
        return (true);

    if (order_type == ORDER_TYPE_BUY)
        return (rates[0].close > rates[0].open);

    if (order_type == ORDER_TYPE_SELL)
        return (rates[0].close < rates[0].open);

    return (false);
}

//+------------------------------------------------------------------+
//| M1 STRUCTURE CONFIRMATION                                        |
//|                                                                  |
//| Uses LAST FULLY CLOSED M1 candle                                 |
//+------------------------------------------------------------------+
bool ConfirmM1Structure(ENUM_ORDER_TYPE order_type)
{
    if (!InpUseM1Filter || !InpUseM1Structure)
        return (true);

    MqlRates rates[1];

    // IMPORTANT:
    // shift 1 = last completed candle
    if (CopyRates(_Symbol, PERIOD_M1, 1, 1, rates) <= 0)
        return (false);

    double high  = rates[0].high;
    double low   = rates[0].low;
    double open  = rates[0].open;
    double close = rates[0].close;

    double range = high - low;

    if (range <= 0.0)
        return (false);

    double body        = MathAbs(close - open);
    double upper_wick  = high - MathMax(open, close);
    double lower_wick  = MathMin(open, close) - low;

    double body_ratio   = body / range;
    double upper_ratio  = upper_wick / range;
    double lower_ratio  = lower_wick / range;

    // Close location:
    // 0.0 = low, 1.0 = high
    double close_location = (close - low) / range;

    //===============================================================
    // SELL
    //===============================================================
    if (order_type == ORDER_TYPE_SELL)
    {
        // Upper rejection
        if (upper_ratio < InpMinWickRatio)
            return (false);

        // Optional body filter
        if (InpMinBodyRatio > 0.0 && body_ratio < InpMinBodyRatio)
            return (false);

        // Optional bearish candle bias
        if (InpRequireCandleBias && close >= open)
            return (false);

        // Optional close location
        if (InpRequireCloseLocation)
        {
            double max_sell_close = 1.0 - InpMinCloseLocation;
            if (close_location > max_sell_close)
                return (false);
        }

        return (true);
    }

    //===============================================================
    // BUY
    //===============================================================
    if (order_type == ORDER_TYPE_BUY)
    {
        // Lower rejection
        if (lower_ratio < InpMinWickRatio)
            return (false);

        // Optional body filter
        if (InpMinBodyRatio > 0.0 && body_ratio < InpMinBodyRatio)
            return (false);

        // Optional bullish candle bias
        if (InpRequireCandleBias && close <= open)
            return (false);

        // Optional close location
        if (InpRequireCloseLocation)
        {
            if (close_location < InpMinCloseLocation)
                return (false);
        }

        return (true);
    }

    return (false);
}

//+------------------------------------------------------------------+
//| CAN OPEN NEW TRADE                                                |
//+------------------------------------------------------------------+
bool CanOpenNewTrade(
    ENUM_ORDER_TYPE order_type,
    double current_price)
{
    // Total positions
    if (CountOpenPositions() >= InpMaxTotalPositions)
        return (false);

    // Directional positions
    if (CountPositionsByDirection(order_type) >= InpMaxPositionsPerDirection)
        return (false);

    // Cooldown
    if (InpUseCooldown && last_entry_time > 0)
    {
        if ((TimeCurrent() - last_entry_time) < InpCooldownSeconds)
            return (false);
    }

    // Minimum distance from previous entry
    if (last_entry_price > 0.0 && InpMinDistanceFromLastEntryPips > 0.0)
    {
        double min_distance = InpMinDistanceFromLastEntryPips * _Point * pips_multiplier;

        if (MathAbs(current_price - last_entry_price) < min_distance)
            return (false);
    }

    // Minimum bars between entries
    if (InpMinBarsBetweenEntries > 0 && last_entry_bar_m5 > 0)
    {
        datetime current_bar = iTime(_Symbol, PERIOD_M5, 0);

        int bars_passed = Bars(_Symbol, PERIOD_M5, last_entry_bar_m5, current_bar);

        if (bars_passed >= 0 && bars_passed < InpMinBarsBetweenEntries)
            return (false);
    }

    return (true);
}

//+------------------------------------------------------------------+
//| COUNT ALL POSITIONS                                               |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
    int count = 0;

    for (int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);

        if (ticket == 0)
            continue;

        if (PositionGetString(POSITION_SYMBOL) != _Symbol)
            continue;

        if ((ulong)PositionGetInteger(POSITION_MAGIC) != InpMagicNumber)
            continue;

        count++;
    }

    return (count);
}

//+------------------------------------------------------------------+
//| COUNT POSITIONS BY DIRECTION                                      |
//+------------------------------------------------------------------+
int CountPositionsByDirection(ENUM_ORDER_TYPE order_type)
{
    int count = 0;

    ENUM_POSITION_TYPE wanted_type;

    if (order_type == ORDER_TYPE_BUY)
        wanted_type = POSITION_TYPE_BUY;
    else if (order_type == ORDER_TYPE_SELL)
        wanted_type = POSITION_TYPE_SELL;
    else
        return (0);

    for (int i = PositionsTotal() - 1; i >= 0; i--)
    {
        ulong ticket = PositionGetTicket(i);

        if (ticket == 0)
            continue;

        if (PositionGetString(POSITION_SYMBOL) != _Symbol)
            continue;

        if ((ulong)PositionGetInteger(POSITION_MAGIC) != InpMagicNumber)
            continue;

        ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

        if (type == wanted_type)
            count++;
    }

    return (count);
}

//+------------------------------------------------------------------+
//| SPREAD FILTER                                                     |
//+------------------------------------------------------------------+
bool IsSpreadAcceptable(const MqlTick &tick)
{
    double spread = tick.ask - tick.bid;
    double spread_pips = spread / (_Point * pips_multiplier);

    return (spread_pips <= InpMaxSpreadPips);
}

//+------------------------------------------------------------------+
//| SESSION FILTER                                                    |
//+------------------------------------------------------------------+
bool IsTradingSessionActive(datetime current_time)
{
    MqlDateTime dt;

    TimeToStruct(current_time, dt);

    // Avoid rollover
    if (InpAvoidRollover)
    {
        if ((dt.hour == 23 && dt.min >= 45) || (dt.hour == 0 && dt.min <= 30))
            return (false);
    }

    if (InpSessionMode == SESSION_ALL_DAY)
        return (true);

    int current_minutes = dt.hour * 60 + dt.min;

    int s1_start = ParseTimeToMinutes(InpSession1_Start);
    int s1_end   = ParseTimeToMinutes(InpSession1_End);
    int s2_start = ParseTimeToMinutes(InpSession2_Start);
    int s2_end   = ParseTimeToMinutes(InpSession2_End);

    bool session1 = IsInsideSession(current_minutes, s1_start, s1_end);
    bool session2 = IsInsideSession(current_minutes, s2_start, s2_end);

    return (session1 || session2);
}

//+------------------------------------------------------------------+
//| SESSION RANGE CHECK                                               |
//+------------------------------------------------------------------+
bool IsInsideSession(
    int current_minutes,
    int start_minutes,
    int end_minutes)
{
    // Normal session
    if (start_minutes <= end_minutes)
    {
        return (current_minutes >= start_minutes && current_minutes <= end_minutes);
    }

    // Overnight session
    return (current_minutes >= start_minutes || current_minutes <= end_minutes);
}

//+------------------------------------------------------------------+
//| PARSE HH:MM                                                       |
//+------------------------------------------------------------------+
int ParseTimeToMinutes(string time_str)
{
    string parts[];

    if (StringSplit(time_str, ':', parts) == 2)
    {
        int hour   = (int)StringToInteger(parts[0]);
        int minute = (int)StringToInteger(parts[1]);

        if (hour < 0)   hour = 0;
        if (hour > 23)  hour = 23;

        if (minute < 0)   minute = 0;
        if (minute > 59)  minute = 59;

        return (hour * 60 + minute);
    }

    return (0);
}

//+------------------------------------------------------------------+
//| CALCULATE TICK VWAP                                               |
//+------------------------------------------------------------------+
void CalculateTickVWAP(
    double &vwap,
    double &std_dev)
{
    double sum_pv = 0.0;
    double sum_v  = 0.0;

    for (int i = 0; i < InpTickBufferSize; i++)
    {
        double mid_price = (tick_buffer[i].bid + tick_buffer[i].ask) / 2.0;
        double volume    = (double)tick_buffer[i].volume;

        sum_pv += mid_price * volume;
        sum_v  += volume;
    }

    if (sum_v <= 0.0)
    {
        vwap    = tick_buffer[0].bid;
        std_dev = 0.0;
        return;
    }

    vwap = sum_pv / sum_v;

    double sum_variance = 0.0;

    for (int i = 0; i < InpTickBufferSize; i++)
    {
        double mid_price = (tick_buffer[i].bid + tick_buffer[i].ask) / 2.0;
        double diff      = mid_price - vwap;

        sum_variance += (double)tick_buffer[i].volume * diff * diff;
    }

    std_dev = MathSqrt(sum_variance / sum_v);
}

//+------------------------------------------------------------------+
//| CALCULATE LOT SIZE                                                |
//+------------------------------------------------------------------+
double CalculateLotSize(
    ENUM_ORDER_TYPE order_type,
    double entry_price,
    double sl_price)
{
    if (InpMMType == MM_FIXED_LOT)
        return (NormalizeLot(InpFixedLot));

    double capital = (InpRiskBase == RISK_BASE_BALANCE)
                        ? AccountInfoDouble(ACCOUNT_BALANCE)
                        : AccountInfoDouble(ACCOUNT_EQUITY);

    if (capital <= 0.0)
        return (NormalizeLot(InpFixedLot));

    double risk_amount = capital * (InpRiskPercent / 100.0);

    if (risk_amount <= 0.0)
        return (NormalizeLot(InpFixedLot));

    // Use OrderCalcProfit for more accurate symbol-specific risk
    double profit_one_lot = 0.0;

    if (!OrderCalcProfit(order_type, _Symbol, 1.0, entry_price, sl_price, profit_one_lot))
    {
        return (CalculateLotSizeFallback(sl_price - entry_price));
    }

    double loss_per_lot = MathAbs(profit_one_lot);

    if (loss_per_lot <= 0.0)
        return (CalculateLotSizeFallback(MathAbs(sl_price - entry_price)));

    double lot = risk_amount / loss_per_lot;

    return (NormalizeLot(lot));
}

//+------------------------------------------------------------------+
//| FALLBACK LOT CALCULATION                                          |
//+------------------------------------------------------------------+
double CalculateLotSizeFallback(double sl_distance)
{
    if (InpMMType == MM_FIXED_LOT)
        return (NormalizeLot(InpFixedLot));

    double capital = (InpRiskBase == RISK_BASE_BALANCE)
                        ? AccountInfoDouble(ACCOUNT_BALANCE)
                        : AccountInfoDouble(ACCOUNT_EQUITY);

    if (capital <= 0.0 || sl_distance <= 0.0)
        return (NormalizeLot(InpFixedLot));

    double risk_amount = capital * (InpRiskPercent / 100.0);

    double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);

    if (tick_value <= 0.0)
        tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);

    double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);

    if (tick_value <= 0.0 || tick_size <= 0.0)
        return (NormalizeLot(InpFixedLot));

    double ticks = sl_distance / tick_size;
    double loss_per_lot = ticks * tick_value;

    if (loss_per_lot <= 0.0)
        return (NormalizeLot(InpFixedLot));

    return (NormalizeLot(risk_amount / loss_per_lot));
}

//+------------------------------------------------------------------+
//| NORMALIZE LOT                                                     |
//+------------------------------------------------------------------+
double NormalizeLot(double lot)
{
    double min_lot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double max_lot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
    double step_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

    if (min_lot <= 0.0)  min_lot = 0.01;
    if (max_lot <= 0.0)  max_lot = 100.0;
    if (step_lot <= 0.0) step_lot = 0.01;

    lot = MathMax(min_lot, MathMin(max_lot, lot));

    lot = MathFloor(lot / step_lot) * step_lot;

    if (lot < min_lot)  lot = min_lot;
    if (lot > max_lot)  lot = max_lot;

    int volume_digits = GetVolumeDigits(step_lot);

    return (NormalizeDouble(lot, volume_digits));
}

//+------------------------------------------------------------------+
//| VOLUME DIGITS                                                     |
//+------------------------------------------------------------------+
int GetVolumeDigits(double step)
{
    if (step >= 1.0)   return (0);
    if (step >= 0.1)   return (1);
    if (step >= 0.01)  return (2);
    if (step >= 0.001) return (3);

    return (4);
}

//+------------------------------------------------------------------+
//| ATR SL DISTANCE                                                   |
//+------------------------------------------------------------------+
double GetATRDistance()
{
    if (handle_atr_m1 == INVALID_HANDLE)
        return (0.0);

    double atr[1];

    if (CopyBuffer(handle_atr_m1, 0, 1, 1, atr) <= 0)
        return (0.0);

    return (atr[0]);
}

//+------------------------------------------------------------------+
//| GET FILLING TYPE                                                  |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING GetFillType()
{
    int filling_mode = (int)SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);

    if ((filling_mode & SYMBOL_FILLING_FOK) != 0)
        return (ORDER_FILLING_FOK);

    if ((filling_mode & SYMBOL_FILLING_IOC) != 0)
        return (ORDER_FILLING_IOC);

    return (ORDER_FILLING_RETURN);
}

//+------------------------------------------------------------------+
//| BROKER STOP DISTANCE                                              |
//+------------------------------------------------------------------+
double GetMinimumStopDistance()
{
    long stops_level  = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
    long freeze_level = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL);

    long max_level = MathMax(stops_level, freeze_level);

    return ((double)max_level * _Point);
}

//+------------------------------------------------------------------+
//| EXECUTE TRADE                                                     |
//+------------------------------------------------------------------+
void ExecuteTrade(
    ENUM_ORDER_TYPE order_type,
    double price,
    double vwap_target)
{
    //===============================================================
    // Determine SL/TP distances
    //===============================================================
    double sl_distance = InpStopLossPips * _Point * pips_multiplier;
    double tp_distance = InpTargetPips   * _Point * pips_multiplier;

    // ATR mode
    if (InpSLTPMode == SLTP_ATR)
    {
        double atr = GetATRDistance();

        if (atr <= 0.0)
        {
            Print("[ENTRY BLOCKED] ATR unavailable.");
            return;
        }

        sl_distance = atr * InpATRMultiplierSL;
        tp_distance = atr * InpATRMultiplierTP;
    }

    if (sl_distance <= 0.0 || tp_distance <= 0.0)
        return;

    // Broker minimum distance
    double min_stop = GetMinimumStopDistance();

    if (sl_distance < min_stop)
        sl_distance = min_stop;

    if (tp_distance < min_stop)
        tp_distance = min_stop;

    //===============================================================
    // Calculate SL / TP
    //===============================================================
    double sl = 0.0;
    double tp = 0.0;

    if (order_type == ORDER_TYPE_BUY)
    {
        sl = price - sl_distance;
        tp = price + tp_distance;

        if (InpUseVWAPTarget && vwap_target > price)
        {
            tp = MathMax(tp, vwap_target);
        }
    }
    else if (order_type == ORDER_TYPE_SELL)
    {
        sl = price + sl_distance;
        tp = price - tp_distance;

        if (InpUseVWAPTarget && vwap_target < price && vwap_target > 0.0)
        {
            tp = MathMin(tp, vwap_target);
        }
    }
    else
        return;

    sl = NormalizeDouble(sl, _Digits);
    tp = NormalizeDouble(tp, _Digits);

    //===============================================================
    // Validate SL / TP
    //===============================================================
    if (order_type == ORDER_TYPE_BUY)
    {
        if (sl >= price || tp <= price)
            return;
    }
    else
    {
        if (sl <= price || tp >= price)
            return;
    }

    //===============================================================
    // Calculate lot
    //===============================================================
    double lot = CalculateLotSize(order_type, price, sl);

    if (lot <= 0.0)
    {
        Print("[ENTRY BLOCKED] Invalid lot size.");
        return;
    }

    //===============================================================
    // Trade request
    //===============================================================
    MqlTradeRequest request = {};
    MqlTradeResult  result  = {};

    request.action   = TRADE_ACTION_DEAL;
    request.symbol   = _Symbol;
    request.volume   = lot;
    request.type     = order_type;
    request.price    = NormalizeDouble(price, _Digits);
    request.sl       = sl;
    request.tp       = tp;
    request.magic    = InpMagicNumber;
    request.deviation = InpDeviationPoints;
    request.type_filling = GetFillType();
    request.comment  = "HybridMicroStruct";

    //===============================================================
    // OrderCheck
    //===============================================================
    MqlTradeCheckResult check = {};

    ResetLastError();

    if (!OrderCheck(request, check))
    {
        PrintFormat(
            "[ORDERCHECK ERROR] Error=%d | Retcode=%u | Comment=%s",
            GetLastError(),
            check.retcode,
            check.comment
        );

        return;
    }

    //===============================================================
    // SEND ORDER
    //===============================================================
    ResetLastError();

    bool sent = OrderSend(request, result);

    if (!sent)
    {
        PrintFormat(
            "[ORDER ERROR] %s | Error=%d | Retcode=%u | Comment=%s",
            OrderTypeToString(order_type),
            GetLastError(),
            result.retcode,
            result.comment
        );

        return;
    }

    // Check actual trade result
    if (result.retcode != TRADE_RETCODE_DONE &&
        result.retcode != TRADE_RETCODE_PLACED &&
        result.retcode != TRADE_RETCODE_DONE_PARTIAL)
    {
        PrintFormat(
            "[ORDER REJECTED] %s | Retcode=%u | Comment=%s",
            OrderTypeToString(order_type),
            result.retcode,
            result.comment
        );

        return;
    }

    //===============================================================
    // Successful entry
    //===============================================================
    last_entry_time   = TimeCurrent();
    last_entry_price  = price;
    last_entry_bar_m5 = iTime(_Symbol, PERIOD_M5, 0);

    PrintFormat(
        "[ORDER SUCCESS] %s | Lot=%.2f | Entry=%.*f | SL=%.*f | TP=%.*f | Ticket=%I64u",
        OrderTypeToString(order_type),
        lot,
        _Digits,
        price,
        _Digits,
        sl,
        _Digits,
        tp,
        result.order
    );
}

//+------------------------------------------------------------------+
//| ORDER TYPE TO STRING                                              |
//+------------------------------------------------------------------+
string OrderTypeToString(ENUM_ORDER_TYPE type)
{
    if (type == ORDER_TYPE_BUY)
        return ("BUY");

    if (type == ORDER_TYPE_SELL)
        return ("SELL");

    return ("UNKNOWN");
}

//+------------------------------------------------------------------+
//| BREAK EVEN & TRAILING (ANTI-LAG & BROKER COMPLIANT)              |
//+------------------------------------------------------------------+
void SecureProfits()
  {
   if(!InpUseTrailing) return;

   // 1. Konversi jarak ke dalam satuan Points MQL5
   double break_even_dist = InpBreakEvenPips    * _Point * pips_multiplier;
   double trailing_dist   = InpTrailingStopPips * _Point * pips_multiplier;
   double trailing_step   = InpTrailingStepPips * _Point * pips_multiplier;
   
   // 2. Tolerance untuk mengatasi Error Floating Point (Desimal)
   double tolerance = _Point * 0.1; 

   // 3. Dapatkan batas minimum pergerakan SL dari Broker
   double stops_level  = (double)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
   double freeze_level = (double)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL) * _Point;
   double min_distance = MathMax(stops_level, freeze_level);

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != InpMagicNumber) continue;

      ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double current_sl = PositionGetDouble(POSITION_SL);
      double current_tp = PositionGetDouble(POSITION_TP);

      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

      double new_sl = current_sl;
      bool modify = false;

      //============================================================
      // BUY POSITION
      //============================================================
      if(type == POSITION_TYPE_BUY)
        {
         double profit_distance = bid - open_price;

         // --- A. Break Even ---
         if(profit_distance >= break_even_dist)
           {
            if(current_sl == 0.0 || current_sl < open_price)
              {
               new_sl = open_price;
               modify = true;
              }
           }

         // --- B. Trailing Stop ---
         if(profit_distance >= trailing_dist)
           {
            double calculated_sl = bid - trailing_dist;

            if(current_sl == 0.0 || calculated_sl > current_sl)
              {
               // FIX: Gunakan tolerance agar kondisi >= tidak digagalkan oleh desimal meleset
               if(current_sl == 0.0 || (calculated_sl - current_sl) >= (trailing_step - tolerance))
                 {
                  new_sl = calculated_sl;
                  modify = true;
                 }
              }
           }

         // Proteksi: Jangan biarkan SL turun di bawah Entry setelah Break Even
         if(current_sl >= open_price && new_sl < open_price) new_sl = open_price;
        }

      //============================================================
      // SELL POSITION
      //============================================================
      else if(type == POSITION_TYPE_SELL)
        {
         double profit_distance = open_price - ask;

         // --- A. Break Even ---
         if(profit_distance >= break_even_dist)
           {
            if(current_sl == 0.0 || current_sl > open_price)
              {
               new_sl = open_price;
               modify = true;
              }
           }

         // --- B. Trailing Stop ---
         if(profit_distance >= trailing_dist)
           {
            double calculated_sl = ask + trailing_dist;

            if(current_sl == 0.0 || calculated_sl < current_sl)
              {
               // FIX: Gunakan tolerance agar kondisi >= tidak digagalkan oleh desimal meleset
               if(current_sl == 0.0 || (current_sl - calculated_sl) >= (trailing_step - tolerance))
                 {
                  new_sl = calculated_sl;
                  modify = true;
                 }
              }
           }

         // Proteksi: Jangan biarkan SL naik di atas Entry setelah Break Even
         if(current_sl <= open_price && current_sl > 0.0 && new_sl > open_price) new_sl = open_price;
        }

      //============================================================
      // EXECUTE MODIFICATION
      //============================================================
      if(modify)
        {
         new_sl = NormalizeDouble(new_sl, _Digits);

         // FIX: Pastikan kita tidak mengirim order yang akan ditolak oleh Broker Stops Level
         if(type == POSITION_TYPE_BUY  && (bid - new_sl) <= min_distance) continue;
         if(type == POSITION_TYPE_SELL && (new_sl - ask) <= min_distance) continue;

         // Hindari error 10025 (No Changes) jika harga lama sama dengan harga baru
         if(NormalizeDouble(MathAbs(current_sl - new_sl), _Digits) > 0.0)
           {
            MqlTradeRequest request = {};
            MqlTradeResult  result  = {};
            
            request.action   = TRADE_ACTION_SLTP;
            request.position = ticket;
            request.symbol   = _Symbol;
            request.sl       = new_sl;
            request.tp       = current_tp; 
            
            if(!OrderSend(request, result))
              {
               PrintFormat("[TRAILING ALERT] Gagal geser SL tiket #%I64u | Error: %d | Jarak Pips: %.1f", 
                           ticket, GetLastError(), MathAbs(new_sl - current_sl) / (_Point * pips_multiplier));
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| MODIFY POSITION SL/TP (ANTI-SPAM & BROKER SAFE)                  |
//+------------------------------------------------------------------+
bool ModifyPositionSLTP(ulong ticket, double sl, double tp)
{
    // 1. Dapatkan SL dan TP saat ini dari server
    double current_sl = PositionGetDouble(POSITION_SL);
    double current_tp = PositionGetDouble(POSITION_TP);

    // 2. Normalisasi semua angka untuk menghindari error presisi desimal (Floating-Point)
    sl = NormalizeDouble(sl, _Digits);
    tp = NormalizeDouble(tp, _Digits);
    current_sl = NormalizeDouble(current_sl, _Digits);
    current_tp = NormalizeDouble(current_tp, _Digits);

    // 3. FILTER ANTI-SPAM (Error 10025 Guard)
    // Jika SL dan TP baru sama persis dengan yang lama, hentikan fungsi sebelum dikirim ke Broker!
    if (sl == current_sl && tp == current_tp)
    {
        return (true); // Anggap sukses karena target SL sudah berada di titik yang diminta
    }

    // 4. Siapkan Request
    MqlTradeRequest request = {};
    MqlTradeResult  result  = {};

    request.action   = TRADE_ACTION_SLTP;
    request.position = ticket;
    request.symbol   = _Symbol;
    request.sl       = sl;
    request.tp       = tp;

    ResetLastError();

    // 5. Eksekusi Order
    if (!OrderSend(request, result))
    {
        int err = GetLastError();
        
        // Pengecualian khusus jika broker secara sepihak membalas "No Changes" (10025)
        if (err == 10025 || result.retcode == TRADE_RETCODE_NO_CHANGES)
            return (true);

        PrintFormat(
            "[SLTP ERROR] Ticket=%I64u | Error=%d | Retcode=%u | Comment=%s",
            ticket, err, result.retcode, result.comment
        );

        return (false);
    }

    // 6. Verifikasi Status Kesuksesan (Banyak broker merespons dengan TRADE_RETCODE_PLACED sebelum DONE)
    if (result.retcode != TRADE_RETCODE_DONE && result.retcode != TRADE_RETCODE_PLACED && result.retcode != TRADE_RETCODE_NO_CHANGES)
    {
        PrintFormat(
            "[SLTP REJECTED] Ticket=%I64u | Retcode=%u | Comment=%s",
            ticket, result.retcode, result.comment
        );

        return (false);
    }

    return (true);
}

//+------------------------------------------------------------------+
//| END OF EA                                                        |
//+------------------------------------------------------------------+

/* Test 2026/05/12
//+------------------------------------------------------------------+
//|                               Hybrid_Microstructure_EA_V1.00.mq5 |
//|                 Engine: Multi-Session M1 + Adaptive Velocity VWAP|
//|                         Feature: Break Even & Trailing Stop Auto |
//+------------------------------------------------------------------+
#property copyright "Copyright©2023. Ritz EAneha©"
#property link      "https://www.mql5.com/en/users/ritzfalih"
#property version   "1.00"
#property strict

//--- ENUM MONEY MANAGEMENT
enum ENUM_MM_TYPE
  {
   MM_FIXED_LOT    = 0, // Fixed Lot Size
   MM_RISK_PERCENT = 1  // Risk Percent (% per Trade)
  };

enum ENUM_RISK_BASE
  {
   RISK_BASE_BALANCE = 0, // Account Balance
   RISK_BASE_EQUITY  = 1  // Account Equity
  };

enum ENUM_SESSION_MODE
  {
   SESSION_ALL_DAY = 0, // Trading All Day (24 Hours)
   SESSION_CUSTOM  = 1  // Custom Trading Sessions (Asia/London/ME)
  };

//--- INPUT PARAMETERS
input group "--- Risk & Money Management ---"
input ulong            InpMagicNumber       = 101010;          
input ENUM_MM_TYPE     InpMMType            = MM_RISK_PERCENT; 
input double           InpFixedLot          = 0.01;            
input double           InpRiskPercent       = 1.0;             
input ENUM_RISK_BASE   InpRiskBase          = RISK_BASE_BALANCE;

input group "--- Execution & Target Settings ---"
input double           InpTargetPips        = 200.0;           
input double           InpStopLossPips      = 120.0;           
input double           InpMaxSpreadPips     = 8.0;             

input group "--- Break Even & Trailing Stop ---"
input bool             InpUseTrailing       = true;            // Aktifkan BE & Trailing
input double           InpBreakEvenPips     = 10.0;            // Break Even Trigger (Pips/100 points)
input double           InpTrailingStopPips  = 15.0;            // Trailing Jarak Aman (Pips/150 points)
input double           InpTrailingStepPips  = 5.0;             // Trailing Step (Pips/50 points)

input group "--- Session & Time Filters ---"
input ENUM_SESSION_MODE InpSessionMode       = SESSION_CUSTOM;  
input string           InpSession1_Start    = "01:00";         
input string           InpSession1_End      = "09:00";         
input string           InpSession2_Start    = "10:00";         
input string           InpSession2_End      = "21:00";         
input bool             InpAvoidRollover     = true;            

input group "--- Microstructure & M1 Filters ---"
input int              InpTickBufferSize    = 500;             
input double           InpDevMultiplier     = 1.2;             
input ulong            InpVelocityWindowMs  = 800;             
input double           InpSnapbackPips      = 2.5;             
input bool             InpUseM1Filter       = true;            
input int              InpM1ATRPeriod       = 14;              
input double           InpMinM1ATRPips      = 1.5;             

//--- STRUCT DATA TICK
struct TickData
  {
   double         bid;
   double         ask;
   ulong          volume;
   long           time_msc;
  };

TickData          tick_buffer[];
int               buffer_index = 0;
bool              buffer_filled = false;
double            pips_multiplier;
int               handle_atr_m1 = INVALID_HANDLE;

bool              is_sweeping_up = false;
bool              is_sweeping_down = false;
double            extreme_peak = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   ArrayResize(tick_buffer, InpTickBufferSize);
   
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   pips_multiplier = (digits == 3 || digits == 5) ? 10.0 : 1.0;

   if(InpUseM1Filter)
     {
      handle_atr_m1 = iATR(_Symbol, PERIOD_M1, InpM1ATRPeriod);
      if(handle_atr_m1 == INVALID_HANDLE) return(INIT_FAILED);
     }

   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   if(handle_atr_m1 != INVALID_HANDLE) IndicatorRelease(handle_atr_m1);
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   MqlTick current_tick;
   if(!SymbolInfoTick(_Symbol, current_tick)) return;
   
   // --- JALANKAN FUNGSI TRAILING STOP & BREAK EVEN ---
   SecureProfits();

   if(!IsTradingSessionActive(current_tick.time)) return;

   double spread_pips = (current_tick.ask - current_tick.bid) / (_Point * pips_multiplier);
   if(spread_pips > InpMaxSpreadPips) return; 

   if(InpUseM1Filter)
     {
      double atr_val[];
      ArraySetAsSeries(atr_val, true);
      if(CopyBuffer(handle_atr_m1, 0, 0, 1, atr_val) > 0)
        {
         double atr_pips = atr_val[0] / (_Point * pips_multiplier);
         if(atr_pips < InpMinM1ATRPips) return; 
        }
     }

   tick_buffer[buffer_index].bid      = current_tick.bid;
   tick_buffer[buffer_index].ask      = current_tick.ask;
   tick_buffer[buffer_index].volume   = (current_tick.volume > 0) ? current_tick.volume : 1;
   tick_buffer[buffer_index].time_msc = current_tick.time_msc;

   buffer_index++;
   if(buffer_index >= InpTickBufferSize)
     {
      buffer_index = 0;
      buffer_filled = true;
     }

   if(!buffer_filled) return;

   double vwap = 0, std_dev = 0;
   CalculateTickVWAP(vwap, std_dev);
   double upper_band = vwap + (std_dev * InpDevMultiplier);
   double lower_band = vwap - (std_dev * InpDevMultiplier);

   int window_size = 10;
   int past_idx = buffer_index - window_size;
   if(past_idx < 0) past_idx += InpTickBufferSize;
   
   long velocity_delta_ms = current_tick.time_msc - tick_buffer[past_idx].time_msc;
   bool is_high_velocity = (velocity_delta_ms > 0 && velocity_delta_ms < (long)InpVelocityWindowMs);

   if(CountOpenPositions() == 0)
     {
      if(current_tick.bid > upper_band && is_high_velocity)
        {
         is_sweeping_up = true;
         is_sweeping_down = false;
         if(current_tick.bid > extreme_peak || extreme_peak == 0) extreme_peak = current_tick.bid;
        }
        
      if(is_sweeping_up)
        {
         double snapback_level = extreme_peak - (InpSnapbackPips * _Point * pips_multiplier);
         if(current_tick.bid <= snapback_level)
           {
            if(ConfirmM1Structure(ORDER_TYPE_SELL)) ExecuteTrade(ORDER_TYPE_SELL, current_tick.bid, vwap);
            is_sweeping_up = false; extreme_peak = 0;
           }
         else if(current_tick.bid < upper_band) { is_sweeping_up = false; extreme_peak = 0; }
        }

      if(current_tick.ask < lower_band && is_high_velocity)
        {
         is_sweeping_down = true;
         is_sweeping_up = false;
         if(current_tick.ask < extreme_peak || extreme_peak == 0) extreme_peak = current_tick.ask;
        }
        
      if(is_sweeping_down)
        {
         double snapback_level = extreme_peak + (InpSnapbackPips * _Point * pips_multiplier);
         if(current_tick.ask >= snapback_level)
           {
            if(ConfirmM1Structure(ORDER_TYPE_BUY)) ExecuteTrade(ORDER_TYPE_BUY, current_tick.ask, vwap);
            is_sweeping_down = false; extreme_peak = 0;
           }
         else if(current_tick.ask > lower_band) { is_sweeping_down = false; extreme_peak = 0; }
        }
     }
   else
     {
      is_sweeping_up = false; 
      is_sweeping_down = false; 
      extreme_peak = 0;
     }
  }

//+------------------------------------------------------------------+
//| FUNGSI TRANSLASI: Break Even & Trailing Stop untuk MT5           |
//+------------------------------------------------------------------+
void SecureProfits()
  {
   if(!InpUseTrailing) return;

   // Konversi input ke format jarak harga sesuai pips/points MT5
   double break_even_dist    = InpBreakEvenPips * _Point * pips_multiplier;
   double trailing_stop_dist = InpTrailingStopPips * _Point * pips_multiplier;
   double trailing_step      = InpTrailingStepPips * _Point * pips_multiplier;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket > 0 && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
        {
         long type = PositionGetInteger(POSITION_TYPE);
         double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
         double current_sl = PositionGetDouble(POSITION_SL);
         double current_tp = PositionGetDouble(POSITION_TP);
         
         double current_bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         double current_ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         
         double new_sl = current_sl;
         bool modify_order = false;

         // --- LOGIKA ORDER BUY ---
         if(type == POSITION_TYPE_BUY)
           {
            // 1. Eksekusi Break Even
            if(current_bid - open_price >= break_even_dist)
              {
               if(current_sl < open_price)
                 {
                  new_sl = open_price;
                  modify_order = true;
                 }
              }
            
            // 2. Eksekusi Trailing Stop
            if(current_bid - open_price >= trailing_stop_dist)
              {
               double calculated_sl = current_bid - trailing_stop_dist;
               if(current_sl < calculated_sl && (calculated_sl - current_sl >= trailing_step || current_sl == open_price))
                 {
                  new_sl = calculated_sl;
                  modify_order = true;
                 }
              }
           }
           
         // --- LOGIKA ORDER SELL ---
         else if(type == POSITION_TYPE_SELL)
           {
            // 1. Eksekusi Break Even
            if(open_price - current_ask >= break_even_dist)
              {
               if(current_sl > open_price || current_sl == 0)
                 {
                  new_sl = open_price;
                  modify_order = true;
                 }
              }
            
            // 2. Eksekusi Trailing Stop
            if(open_price - current_ask >= trailing_stop_dist)
              {
               double calculated_sl = current_ask + trailing_stop_dist;
               if(current_sl > calculated_sl || current_sl == 0)
                 {
                  if(current_sl - calculated_sl >= trailing_step || current_sl == open_price)
                    {
                     new_sl = calculated_sl;
                     modify_order = true;
                    }
                 }
              }
           }
           
         // --- MODIFIKASI ORDER MT5 ---
         if(modify_order)
           {
            MqlTradeRequest request = {};
            MqlTradeResult  result  = {};
            
            request.action   = TRADE_ACTION_SLTP;
            request.position = ticket;
            request.symbol   = _Symbol;
            request.sl       = NormalizeDouble(new_sl, _Digits);
            request.tp       = current_tp; // TP dibiarkan tetap
            
            if(!OrderSend(request, result))
              {
               Print("[TRAILING ERROR] Gagal modifikasi SL tiket #", ticket, " Error: ", GetLastError());
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| Filter Sesi Trading & Jam Operasional Server                     |
//+------------------------------------------------------------------+
bool IsTradingSessionActive(datetime current_time)
  {
   MqlDateTime dt;
   TimeToStruct(current_time, dt);
   if(InpAvoidRollover)
     {
      if((dt.hour == 23 && dt.min >= 45) || (dt.hour == 0 && dt.min <= 30)) return false;
     }
   if(InpSessionMode == SESSION_ALL_DAY) return true;
   int current_minutes = dt.hour * 60 + dt.min;
   int s1_start = ParseTimeToMinutes(InpSession1_Start);
   int s1_end   = ParseTimeToMinutes(InpSession1_End);
   int s2_start = ParseTimeToMinutes(InpSession2_Start);
   int s2_end   = ParseTimeToMinutes(InpSession2_End);
   return ((current_minutes >= s1_start && current_minutes <= s1_end) || (current_minutes >= s2_start && current_minutes <= s2_end));
  }

int ParseTimeToMinutes(string time_str)
  {
   string parts[];
   if(StringSplit(time_str, ':', parts) == 2) return ((int)StringToInteger(parts[0]) * 60) + (int)StringToInteger(parts[1]);
   return 0;
  }

bool ConfirmM1Structure(ENUM_ORDER_TYPE order_type)
  {
   if(!InpUseM1Filter) return true;
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, PERIOD_M1, 0, 1, rates) <= 0) return true;
   if(order_type == ORDER_TYPE_SELL)
     {
      double candle_range = rates[0].high - rates[0].low;
      if(candle_range <= 0) return true;
      double upper_wick = rates[0].high - MathMax(rates[0].open, rates[0].close);
      return (upper_wick / candle_range) >= 0.20; 
     }
   if(order_type == ORDER_TYPE_BUY)
     {
      double candle_range = rates[0].high - rates[0].low;
      if(candle_range <= 0) return true;
      double lower_wick = MathMin(rates[0].open, rates[0].close) - rates[0].low;
      return (lower_wick / candle_range) >= 0.20; 
     }
   return true;
  }

void CalculateTickVWAP(double &vwap, double &std_dev)
  {
   double sum_pv = 0, sum_v = 0;
   for(int i = 0; i < InpTickBufferSize; i++)
     {
      double mid_price = (tick_buffer[i].bid + tick_buffer[i].ask) / 2.0;
      sum_pv += mid_price * (double)tick_buffer[i].volume;
      sum_v  += (double)tick_buffer[i].volume;
     }
   vwap = (sum_v > 0) ? (sum_pv / sum_v) : tick_buffer[0].bid;
   double sum_variance = 0;
   for(int i = 0; i < InpTickBufferSize; i++)
     {
      double mid_price = (tick_buffer[i].bid + tick_buffer[i].ask) / 2.0;
      double diff = mid_price - vwap;
      sum_variance += (double)tick_buffer[i].volume * (diff * diff);
     }
   std_dev = (sum_v > 0) ? MathSqrt(sum_variance / sum_v) : 0;
  }

int CountOpenPositions()
  {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber) count++;
     }
   return count;
  }

double CalculateLotSize(double sl_distance)
  {
   if(InpMMType == MM_FIXED_LOT) return NormalizeLot(InpFixedLot);
   double capital = (InpRiskBase == RISK_BASE_BALANCE) ? AccountInfoDouble(ACCOUNT_BALANCE) : AccountInfoDouble(ACCOUNT_EQUITY);
   if(capital <= 0 || sl_distance <= 0) return NormalizeLot(InpFixedLot);
   double risk_amount = capital * (InpRiskPercent / 100.0);
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tick_value <= 0) tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick_size <= 0 || tick_value <= 0) return NormalizeLot(InpFixedLot);
   double ticks_in_sl = sl_distance / tick_size;
   double loss_per_lot = ticks_in_sl * tick_value;
   if(loss_per_lot <= 0) return NormalizeLot(InpFixedLot);
   double calculated_lot = risk_amount / loss_per_lot;
   return NormalizeLot(calculated_lot);
  }

double NormalizeLot(double lot)
  {
   double min_lot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step_lot <= 0) step_lot = 0.01;
   double normalized = MathFloor(lot / step_lot) * step_lot;
   if(normalized < min_lot) normalized = min_lot;
   if(normalized > max_lot) normalized = max_lot;
   return NormalizeDouble(normalized, 2);
  }

ENUM_ORDER_TYPE_FILLING GetFillType()
  {
   int filling_mode = (int)SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   if((filling_mode & SYMBOL_FILLING_FOK) != 0) return ORDER_FILLING_FOK;
   if((filling_mode & SYMBOL_FILLING_IOC) != 0) return ORDER_FILLING_IOC;
   return ORDER_FILLING_RETURN;
  }

void ExecuteTrade(ENUM_ORDER_TYPE order_type, double price, double vwap_target)
  {
   MqlTradeRequest request = {};
   MqlTradeResult  result  = {};
   double sl_distance = InpStopLossPips * _Point * pips_multiplier;
   double tp_distance = InpTargetPips * _Point * pips_multiplier;
   double lot_size = CalculateLotSize(sl_distance);
   request.action       = TRADE_ACTION_DEAL;
   request.symbol       = _Symbol;
   request.volume       = lot_size;
   request.type         = order_type;
   request.price        = price;
   request.magic        = InpMagicNumber;
   request.deviation    = 20; 
   request.type_filling = GetFillType(); 
   if(order_type == ORDER_TYPE_BUY)
     {
      request.sl = NormalizeDouble(price - sl_distance, _Digits);
      request.tp = NormalizeDouble(MathMax(price + tp_distance, vwap_target), _Digits);
     }
   else
     {
      request.sl = NormalizeDouble(price + sl_distance, _Digits);
      request.tp = NormalizeDouble(MathMin(price - tp_distance, vwap_target), _Digits);
     }
   if(!OrderSend(request, result))
     {
      PrintFormat("[ORDER ERROR] Gagal Eksekusi %s! Lot: %.2f | Error: %d | Bid: %.3f | Ask: %.3f", 
                  (order_type == ORDER_TYPE_BUY ? "BUY" : "SELL"), lot_size, GetLastError(), SymbolInfoDouble(_Symbol, SYMBOL_BID), SymbolInfoDouble(_Symbol, SYMBOL_ASK));
     }
   else
     {
      PrintFormat("[ORDER SUCCESS] %s Terpasang! Lot: %.2f | Ticket: %I64u | SL: %.3f | TP: %.3f", 
                  (order_type == ORDER_TYPE_BUY ? "BUY" : "SELL"), lot_size, result.order, request.sl, request.tp);
     }
  }
//+------------------------------------------------------------------+

*/