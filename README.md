
## ⚠️ Disclaimer

This project is for **educational and research purposes only**. It does **not constitute financial advice** or a recommendation to trade. Use it at your own risk.

We make **no guarantees** about performance, profitability, or safety. You are solely responsible for any outcomes, and must ensure compliance with applicable laws and regulations.



# MM

This MM bot is heavily inspired by https://github.com/blockworks-foundation/mango-explorer/
its goal and purpose is to be an educational material to whoever wants to learn about market making
and about Starknet.

The bot is currently operational, but a lot of work is required.

Missing features:
- Json logging + log more info.
- Handle "out of liquidity" situations.
- Implement max_fee (or rather ResourceBounds in case of invoke_v3)

- Create new reconciliation logic. Current version doesn't account for inflight orders.
- Consider to connect to wss, rather than API.
- Build simple viewer/debugger of the past.

- Handle multiple accounts.
- Handle multiple markets per DEX.
- Handle multiple DEXes.
