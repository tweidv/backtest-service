# Trade History

> Fetches historical trade data for Kalshi markets with optional filtering by **ticker** and time range. Returns executed trades with pricing, volume, and taker side information. All timestamps are in **seconds**.



## OpenAPI

````yaml api-reference/openapi.json get /kalshi/trades
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /kalshi/trades:
    get:
      summary: Get Kalshi Trades
      description: >-
        Fetches historical trade data for Kalshi markets with optional filtering
        by ticker and time range. Returns executed trades with pricing, volume,
        and taker side information. All timestamps are in seconds.
      operationId: getKalshiTrades
      parameters:
        - name: ticker
          in: query
          required: false
          description: The Kalshi market ticker to filter trades
          schema:
            type: string
            example: KXNFLGAME-25NOV09PITLAC-PIT
        - name: start_time
          in: query
          required: false
          description: Start time in Unix timestamp (seconds)
          schema:
            type: integer
            example: 1762716000
        - name: end_time
          in: query
          required: false
          description: End time in Unix timestamp (seconds)
          schema:
            type: integer
            example: 1762720600
        - name: limit
          in: query
          required: false
          description: 'Maximum number of trades to return (default: 100)'
          schema:
            type: integer
            default: 100
            example: 10
        - name: offset
          in: query
          required: false
          description: Number of trades to skip for pagination
          schema:
            type: integer
            minimum: 0
            default: 0
            example: 0
      responses:
        '200':
          description: Kalshi trades response with pagination
          content:
            application/json:
              schema:
                type: object
                properties:
                  trades:
                    type: array
                    description: Array of executed trades
                    items:
                      type: object
                      properties:
                        trade_id:
                          type: string
                          description: Unique identifier for the trade
                          example: 587f9eb0-1ae1-7b53-9536-fcf3fc503630
                        market_ticker:
                          type: string
                          description: The Kalshi market ticker
                          example: KXNFLGAME-25NOV09PITLAC-PIT
                        count:
                          type: integer
                          description: Number of contracts traded
                          example: 93
                        yes_price:
                          type: integer
                          description: Yes side price in cents
                          example: 1
                        no_price:
                          type: integer
                          description: No side price in cents
                          example: 99
                        yes_price_dollars:
                          type: number
                          description: Yes side price in dollars
                          example: 0.01
                        no_price_dollars:
                          type: number
                          description: No side price in dollars
                          example: 0.99
                        taker_side:
                          type: string
                          description: Which side was the taker (yes or no)
                          enum:
                            - 'yes'
                            - 'no'
                          example: 'yes'
                        created_time:
                          type: integer
                          description: Timestamp of the trade in seconds (Unix timestamp)
                          example: 1762718746
                  pagination:
                    type: object
                    properties:
                      limit:
                        type: integer
                        example: 50
                      offset:
                        type: integer
                        example: 100
                      total:
                        type: integer
                        description: Total number of trades matching the filters
                        example: 43154
                      has_more:
                        type: boolean
                        description: Whether there are more trades available
                        example: true
        '400':
          description: Bad Request - Invalid parameters
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Invalid parameters
                  message:
                    type: string
                    example: Invalid time range or parameters

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt