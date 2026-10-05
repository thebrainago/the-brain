from da_agent.chay import chay
import sys
if len(sys.argv) >= 3 and sys.argv[1] == "chay":
    chay(sys.argv[2])
else:
    print("dung: python3 -m da_agent chay <ke_hoach.json>")
