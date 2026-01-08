# Binance Prices

> Fetches historical crypto price data from Binance. Returns price data for a specific currency pair over an optional time range. When no time range is provided, returns the most recent price. All timestamps are in Unix milliseconds. Currency format: lowercase alphanumeric with no separators (e.g., btcusdt, ethusdt).



## OpenAPI

````yaml api-reference/openapi.json get /crypto-prices/binance
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /crypto-prices/binance:
    get:
      summary: Get Binance Crypto Prices
      description: >-
        Fetches historical crypto price data from Binance. Returns price data
        for a specific currency pair over an optional time range. When no time
        range is provided, returns the most recent price (limit 1). All
        timestamps are in Unix milliseconds.


        **Currency Format:** Lowercase, no separators (e.g., `btcusdt`,
        `ethusdt`, `solusdt`, `xrpusdt`)


        **Example Request (Latest Price):**

        ```bash

        curl 'https://api.domeapi.io/v1/crypto-prices/binance?currency=btcusdt'
        \
          -H 'Authorization: Bearer YOUR_TOKEN'
        ```


        **Example Request (Time Range):**

        ```bash

        curl
        'https://api.domeapi.io/v1/crypto-prices/binance?currency=btcusdt&start_time=1766130000000&end_time=1766131000000&limit=10'
        \
          -H 'Authorization: Bearer YOUR_TOKEN'
        ```
      operationId: getBinanceCryptoPrices
      parameters:
        - name: currency
          in: query
          required: true
          description: >-
            The currency pair symbol. Must be lowercase alphanumeric with no
            separators (e.g., `btcusdt`, `ethusdt`, `solusdt`, `xrpusdt`).
          schema:
            type: string
            pattern: ^[a-z0-9]+$
            example: btcusdt
        - name: start_time
          in: query
          required: false
          description: >-
            Start time in Unix timestamp (milliseconds). If not provided along
            with end_time, returns the most recent price (limit 1).
          schema:
            type: integer
            example: 1766130000000
        - name: end_time
          in: query
          required: false
          description: >-
            End time in Unix timestamp (milliseconds). If not provided along
            with start_time, returns the most recent price (limit 1).
          schema:
            type: integer
            example: 1766131000000
        - name: limit
          in: query
          required: false
          description: >-
            Maximum number of prices to return (default: 100, max: 100). When no
            time range is provided, limit is automatically set to 1.
          schema:
            type: integer
            default: 100
            minimum: 1
            maximum: 100
            example: 10
        - name: pagination_key
          in: query
          required: false
          description: >-
            Pagination key (base64-encoded) to fetch the next page of results.
            Returned in the response when more data is available.
          schema:
            type: string
            example: eyJpZCI6IlBSSUNFI2J0Y3VzZHQiLCJ0aW1lc3RhbXAiOjE3NjYxMzEwMDAwMDB9
      responses:
        '200':
          description: Crypto prices response
          content:
            application/json:
              schema:
                type: object
                properties:
                  prices:
                    type: array
                    description: Array of crypto price data points
                    items:
                      type: object
                      properties:
                        symbol:
                          type: string
                          description: The currency pair symbol
                          example: btcusdt
                        value:
                          oneOf:
                            - type: string
                            - type: number
                          description: The price value
                          example: '67500.50'
                        timestamp:
                          type: integer
                          description: >-
                            Unix timestamp in milliseconds when the price was
                            recorded
                          example: 1766130500000
                      required:
                        - symbol
                        - value
                        - timestamp
                  pagination_key:
                    type: string
                    description: >-
                      Pagination key (base64-encoded) to fetch the next page of
                      results. Only present when more data is available.
                    example: >-
                      eyJpZCI6IlBSSUNFI2J0Y3VzZHQiLCJ0aW1lc3RhbXAiOjE3NjYxMzEwMDAwMDB9
                  total:
                    type: integer
                    description: Total number of prices returned in this response
                    example: 10
                required:
                  - prices
              examples:
                latest_price:
                  summary: Latest price (no time range)
                  description: >-
                    Response when no time range is provided - returns the most
                    recent price
                  value:
                    prices:
                      - symbol: btcusdt
                        value: '67500.50'
                        timestamp: 1766130500000
                    total: 1
                time_range:
                  summary: Time range query
                  description: Response when time range is provided
                  value:
                    prices:
                      - symbol: btcusdt
                        value: '67450.25'
                        timestamp: 1766130000000
                      - symbol: btcusdt
                        value: '67500.50'
                        timestamp: 1766130500000
                      - symbol: btcusdt
                        value: '67525.75'
                        timestamp: 1766131000000
                    total: 3
                with_pagination:
                  summary: Response with pagination
                  description: >-
                    Response when more data is available (pagination_key
                    present)
                  value:
                    prices:
                      - symbol: btcusdt
                        value: '67500.50'
                        timestamp: 1766130000000
                    pagination_key: >-
                      eyJpZCI6IlBSSUNFI2J0Y3VzZHQiLCJ0aW1lc3RhbXAiOjE3NjYxMzEwMDAwMDB9
                    total: 100
        '400':
          description: Bad Request - Invalid parameters or validation errors
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Invalid type parameter
                  message:
                    type: string
                    example: type must be either "binance" or "chainlink"
              examples:
                missing_currency:
                  summary: Missing currency parameter
                  value:
                    error: Missing currency parameter
                    message: currency is required
                invalid_currency_format:
                  summary: Invalid currency format for Binance
                  value:
                    error: Invalid currency format for binance
                    message: >-
                      Binance currency must be lowercase alphanumeric (e.g.,
                      btcusdt)
                invalid_start_time:
                  summary: Invalid start_time parameter
                  value:
                    error: Invalid start_time parameter
                    message: start_time must be a valid Unix timestamp in milliseconds
                invalid_end_time:
                  summary: Invalid end_time parameter
                  value:
                    error: Invalid end_time parameter
                    message: end_time must be a valid Unix timestamp in milliseconds
                invalid_time_range:
                  summary: Invalid time range
                  value:
                    error: Invalid time range
                    message: start_time must be less than or equal to end_time
                invalid_limit:
                  summary: Invalid limit parameter
                  value:
                    error: Invalid limit parameter
                    message: limit must be a positive integer
                invalid_pagination_key:
                  summary: Invalid pagination key
                  value:
                    error: Invalid pagination key format
                    message: Invalid pagination key format
        '404':
          description: Not Found - DynamoDB table not found
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Internal Server Error
                  message:
                    type: string
                    example: >-
                      DynamoDB table not found. Please ensure the table exists
                      and the table name is correct.
        '500':
          description: Internal Server Error
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Internal Server Error
                  message:
                    type: string
                    example: Failed to fetch crypto prices

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt