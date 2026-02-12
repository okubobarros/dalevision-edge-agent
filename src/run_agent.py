import sys

def main():
    # Import absoluto do pacote
    from dalevision_edge_agent.main import main as agent_main
    return agent_main()

if __name__ == "__main__":
    raise SystemExit(main())
