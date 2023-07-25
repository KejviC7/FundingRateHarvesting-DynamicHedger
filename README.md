# FundingRateHarvesting-DynamicHedger
A Funding Rate Harvesting Bot with Dynamic Hedging/Margin Allocation

MEXC has disabled Futures API for quite some time now. However, the bot's logic can translate to other exchanges. 
You would need to make some API call changes.

How does this work?
Funding Rate Harvesting in Crypto is great opportunity for passive income especially when combined with a Dynamic Hedger.
Due to the disrepancy in price between the Spot and Futures markets of a cryptocurrency, the funding rate will be positive/negative.

If we open a Spot position, we are Long. In order to hedge our position, we can open the equivalent in Short in Perpetuals to be completely hedged.
If our Perpetuals/Futures position is Short, and the funding rate is Positive, that means that we will get paid that Funding Rate.
Since we are completely hedged we hold no exposure to the market volatility. 

Of course, in events of extreme volatility, our Short position may get liquidated. To prevent that the bot keeps track of the margin requirement
and liquidation level and dynamically adjusts margin based on the safety buffer we have specified. If we are running out of funds to put up as collateral, 
then the bot will start reducing positions to prevent a potential liquidation and a break of our hedge.

Feel free to reach out to me if you have any questions!
