# Dome API

> Welcome to Dome - the ultimate API for prediction markets

## What is Dome API?

Dome API provides comprehensive access to prediction market data across multiple platforms including Polymarket and Kalshi. Get real-time market prices, historical candlestick data, wallet analytics, order tracking, and cross-platform market matching. Get started with a free API key [here](https://dashboard.domeapi.io/).

## Tier Limits

Rate limits are tiered by subscription level:

| Tier           | Queries Per Second | Queries Per 10 Seconds |
| -------------- | ------------------ | ---------------------- |
| **Free**       | 1                  | 10                     |
| **Dev**        | 100                | 500                    |
| **Enterprise** | Custom             | Custom                 |

## Quick Start

### 1. Get Your API Key

[Sign up](https://dashboard.domeapi.io/) for an account and get your API Key from the dashboard.
<img src="https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=fa7ef3bac84721e7d4366ad8207f8068" alt="Hero Light Pn" data-og-width="2064" width="2064" data-og-height="1104" height="1104" data-path="images/hero-light.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=280&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=6916e9095018482f82cc49f0d97a6678 280w, https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=560&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=d7d6008b151a1bb7bb840ba37adb4758 560w, https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=840&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=831ff585efef02cc968263af252ced44 840w, https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=1100&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=48487615fcbcb8744494547ccbdd6e27 1100w, https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=1650&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=3ed53781014805fa0125c20e9684de3e 1650w, https://mintcdn.com/dome/IMjIL8frwMJgJNzZ/images/hero-light.png?w=2500&fit=max&auto=format&n=IMjIL8frwMJgJNzZ&q=85&s=52761c1fee79e3a6020f443be795512a 2500w" />

### 2. Install SDK

<CodeGroup>
  ```bash TypeScript theme={null}
  npm install @dome-api/sdk
  ```

  ```bash Python theme={null}
  pip install dome-api-sdk
  ```
</CodeGroup>

### 3. Make Your First Request

<CodeGroup>
  ```typescript TypeScript theme={null}
  import { DomeClient } from '@dome-api/sdk';

  const dome = new DomeClient({
  apiKey: 'your-api-key-here',
  });

  const marketPrice = await dome.polymarket.markets.getMarketPrice({
  token_id: '98250445447699368679516529207365255018790721464590833209064266254238063117329',
  });

  console.log('Market Price:', marketPrice.price);

  ```

  ```python Python theme={null}
  from dome_api_sdk import DomeClient

  dome = DomeClient({"api_key": "your-api-key-here"})

  market_price = dome.polymarket.markets.get_market_price({
      "token_id": "98250445447699368679516529207365255018790721464590833209064266254238063117329"
  })
  print(f"Market Price: {market_price.price}")
  ```
</CodeGroup>

## Need Help?

* Join our [Discord](https://discord.gg/fKAbjNAbkt) community
* Check out our SDKs: [TypeScript](https://github.com/kurushdubash/dome-sdk-ts) | [Python](https://github.com/kurushdubash/dome-sdk-py)


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt