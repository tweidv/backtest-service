# Orderbook History

> Fetches historical orderbook snapshots for a specific asset (**token ID**) over a specified time range. If no **start_time** and **end_time** are provided, returns the latest orderbook snapshot for the market. Returns snapshots of the order book including bids, asks, and market metadata in order. All timestamps are in **milliseconds**. Orderbook data has history starting from **October 14th, 2025**. **Note:** When fetching the latest orderbook (without start/end times), the limit and pagination_key parameters are ignored.



## OpenAPI

````yaml api-reference/openapi.json get /polymarket/orderbooks
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /polymarket/orderbooks:
    get:
      summary: Get Orderbook History
      description: >-
        Fetches historical orderbook snapshots for a specific asset (token ID)
        over a specified time range. If no start_time and end_time are provided,
        returns the latest orderbook snapshot for the market. Returns snapshots
        of the order book including bids, asks, and market metadata in order.
        All timestamps are in milliseconds. Orderbook data has history starting
        from October 14th, 2025. Note: When fetching the latest orderbook
        (without start/end times), the limit and pagination_key parameters are
        ignored.
      operationId: getOrderbooks
      parameters:
        - name: token_id
          in: query
          required: true
          description: The token id (asset) for the Polymarket market
          schema:
            type: string
            example: >-
              56369772478534954338683665819559528414197495274302917800610633957542171787417
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
        - name: pagination_key
          in: query
          required: false
          description: >-
            Pagination key to get the next chunk of data. Ignored when fetching
            the latest orderbook without start_time and end_time.
          schema:
            type: string
            example: >-
              eyJhc3NldElkIjoiMTM1ODUxMjc2NDY0NTMxMDM0ODcyMjY1MTg3ODYyNjk5NjE0MDAyMjI5NzA0NzI3MzgxMTIwOTU1NDY0MDc5MTY4NDcxMTIyNzE2NjQiLCJ0aW1lc3RhbXAiOjE3NjExMDQwOTg5MTR9
      responses:
        '200':
          description: Orderbook history response
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
                        asks:
                          type: array
                          description: Sell orders, ordered by price
                          items:
                            type: object
                            properties:
                              size:
                                type: string
                                example: '5000013.15'
                              price:
                                type: string
                                example: '0.999'
                        bids:
                          type: array
                          description: Buy orders, ordered by price
                          items:
                            type: object
                            properties:
                              size:
                                type: string
                                example: '438389.53'
                              price:
                                type: string
                                example: '0.001'
                        hash:
                          type: string
                          example: 85c493ebeea97e2f70c85a1469aede05f892408f
                        minOrderSize:
                          type: string
                          example: '5'
                        negRisk:
                          type: boolean
                          example: true
                        assetId:
                          type: string
                          example: >-
                            56369772478534954338683665819559528414197495274302917800610633957542171787417
                        timestamp:
                          type: integer
                          description: Timestamp of the snapshot in milliseconds
                          example: 1760471849407
                        tickSize:
                          type: string
                          example: '0.001'
                        indexedAt:
                          type: integer
                          description: When the snapshot was indexed in milliseconds
                          example: 1760471852863
                        market:
                          type: string
                          example: >-
                            0xd10bc768ede58b53ed400594240b0a0603134a32dab89ec823a18759cbc180ca
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
                      pagination_key:
                        type: string
                        description: >-
                          The pagination key to pass in to get the next chunk of
                          data
                        example: >-
                          eyJhc3NldElkIjoiMTM1ODUxMjc2NDY0NTMxMDM0ODcyMjY1MTg3ODYyNjk5NjE0MDAyMjI5NzA0NzI3MzgxMTIwOTU1NDY0MDc5MTY4NDcxMTIyNzE2NjQiLCJ0aW1lc3RhbXAiOjE3NjExMDQwOTg5MTR9
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
                    example: assetId, start_time, and end_time are required

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt