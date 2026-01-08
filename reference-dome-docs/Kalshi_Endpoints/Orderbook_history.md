# Orderbook History

> Fetches historical orderbook snapshots for a specific Kalshi market (**ticker**) over a specified time range. If no **start_time** and **end_time** are provided, returns the latest orderbook snapshot for the market. Returns snapshots of the order book including yes/no bids and asks with prices in both cents and dollars. All timestamps are in **milliseconds**. Orderbook data has history starting from **October 29th, 2025**. **Note:** When fetching the latest orderbook (without start/end times), the limit parameter is ignored.



## OpenAPI

````yaml api-reference/openapi.json get /kalshi/orderbooks
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /kalshi/orderbooks:
    get:
      summary: Get Kalshi Orderbook History
      description: >-
        Fetches historical orderbook snapshots for a specific Kalshi market
        (ticker) over a specified time range. If no start_time and end_time are
        provided, returns the latest orderbook snapshot for the market. Returns
        snapshots of the order book including yes/no bids and asks with prices
        in both cents and dollars. All timestamps are in milliseconds. Orderbook
        data has history starting from October 29th, 2025. Note: When fetching
        the latest orderbook (without start/end times), the limit parameter is
        ignored.
      operationId: getKalshiOrderbooks
      parameters:
        - name: ticker
          in: query
          required: true
          description: The Kalshi market ticker
          schema:
            type: string
            example: KXNFLGAME-25AUG16ARIDEN-ARI
        - name: start_time
          in: query
          required: false
          description: >-
            Start time in Unix timestamp (milliseconds). Optional - if not
            provided along with end_time, returns the latest orderbook snapshot.
          schema:
            type: integer
            example: 1760470000000
        - name: end_time
          in: query
          required: false
          description: >-
            End time in Unix timestamp (milliseconds). Optional - if not
            provided along with start_time, returns the latest orderbook
            snapshot.
          schema:
            type: integer
            example: 1760480000000
        - name: limit
          in: query
          required: false
          description: >-
            Maximum number of snapshots to return (default: 100, max: 200).
            Ignored when fetching the latest orderbook without start_time and
            end_time.
          schema:
            type: integer
            default: 100
            maximum: 200
            example: 100
      responses:
        '200':
          description: Kalshi orderbook history response
          content:
            application/json:
              schema:
                type: object
                properties:
                  snapshots:
                    type: array
                    description: Array of orderbook snapshots at different points in time
                    items:
                      type: object
                      properties:
                        orderbook:
                          type: object
                          properties:
                            'yes':
                              type: array
                              description: Yes side orders with prices in cents
                              items:
                                type: array
                                description: '[price_in_cents, contract_count]'
                                items:
                                  type: number
                                minItems: 2
                                maxItems: 2
                                example:
                                  - 75
                                  - 100
                            'no':
                              type: array
                              description: No side orders with prices in cents
                              items:
                                type: array
                                description: '[price_in_cents, contract_count]'
                                items:
                                  type: number
                                minItems: 2
                                maxItems: 2
                                example:
                                  - 25
                                  - 100
                            yes_dollars:
                              type: array
                              description: Yes side orders with prices in dollars
                              items:
                                type: array
                                description: '[price_as_dollar_string, contract_count]'
                                minItems: 2
                                maxItems: 2
                                items:
                                  oneOf:
                                    - type: string
                                    - type: number
                                example:
                                  - '0.75'
                                  - 100
                            no_dollars:
                              type: array
                              description: No side orders with prices in dollars
                              items:
                                type: array
                                description: '[price_as_dollar_string, contract_count]'
                                minItems: 2
                                maxItems: 2
                                items:
                                  oneOf:
                                    - type: string
                                    - type: number
                                example:
                                  - '0.25'
                                  - 100
                        timestamp:
                          type: integer
                          description: Timestamp of the snapshot in milliseconds
                          example: 1760471849407
                        ticker:
                          type: string
                          description: The Kalshi market ticker
                          example: KXNFLGAME-25AUG16ARIDEN-ARI
                  pagination:
                    type: object
                    properties:
                      limit:
                        type: integer
                        example: 100
                      count:
                        type: integer
                        description: Number of snapshots returned
                        example: 4
                      has_more:
                        type: boolean
                        description: Whether there are more snapshots available
                        example: false
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
                    example: ticker, start_time, and end_time are required

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt