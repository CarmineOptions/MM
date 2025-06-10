
## ⚠️ Disclaimer

This project is for **educational and research purposes only**. It does **not constitute financial advice** or a recommendation to trade. Use it at your own risk.

We make **no guarantees** about performance, profitability, or safety. You are solely responsible for any outcomes, and must ensure compliance with applicable laws and regulations.



# MM

This MM bot is heavily inspired by https://github.com/blockworks-foundation/mango-explorer/
its goal and purpose is to be an educational material to whoever wants to learn about market making
and about Starknet.

The bot is currently operational, but a lot of work is required.

Missing features:
- Log into json, rather than .log file.
- Better price fetching.
- Create standardized connector to source data.
- Handle "out of liquidity" situations.
- Create and use some "InstrumentAmount" class that will carry info about denomination token etc.
- add some setup validation
  - eg. all ABCs inherit from abc SetupValidator with method `validate_setup` that is called by market maker during initialization
- In Market class, add execution of orders. Instead of calling invoke in reconciler, call "invoke" on our custom Market method (where one of the params is WAccount).
- Add abstract classes.
- Separate logic in POCMMModel. One part is creation of optimal orders separate part is reconciliation.
- Change v1 invoke to current version of invoke. Invoke from account with dex address, rather than dex Contract, with account already in place.
- Remove f-strings from logging.
- Implement max_fee (or rather ResourceBounds in case of invoke_v3)
- When fetching fp, store info about when it was produces and check was stale prices
- The bot is being prepared to handle multiple accounts. The work is half way done, meaning this is feature is not ready.
- Handle multiple markets per DEX.
- Handle multiple DEXes.

- Create new reconciliation logic. Current version doesn't account for inflight orders.
- Consider to connect to wss, rather than API.
- Build simple viewer/debugger of the past.

Known bugs:
- DOG/wBTC cancels orders because of insufficient order size. This is likely caused by incorrectly handeling the decimals.
