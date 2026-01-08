# Market Price

> Fetches the current market price for a market by token_id. Allows historical lookups via the at_time query parameter.



## OpenAPI

````yaml api-reference/openapi.json get /polymarket/market-price/{token_id}
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /polymarket/market-price/{token_id}:
    parameters:
      - name: token_id
        in: path
        required: true
        description: The token ID for the Polymarket market
        schema:
          type: string
          example: >-
            19701256321759583954581192053894521654935987478209343000964756587964612528044
    get:
      summary: Get Market Price
      description: >-
        Fetches the current market price for a market by `token_id`. When
        `at_time` is not provided, returns the most real-time price available.
        When `at_time` is provided, returns the historical market price at that
        specific timestamp.


        **Example Request (with historical timestamp):**

        ```bash

        curl
        'https://api.domeapi.io/v1/polymarket/market-price/19701256321759583954581192053894521654935987478209343000964756587964612528044?at_time=1762164600'

        ```


        **Example Request (real-time price):**

        ```bash

        curl
        'https://api.domeapi.io/v1/polymarket/market-price/19701256321759583954581192053894521654935987478209343000964756587964612528044'

        ```
      operationId: getMarketPrice
      parameters:
        - name: at_time
          in: query
          required: false
          description: >-
            Optional Unix timestamp (in seconds) to fetch a historical market
            price. If not provided, returns the most real-time price available.
          schema:
            type: integer
            example: 1762164600
      responses:
        '200':
          description: Market price response
          content:
            application/json:
              schema:
                type: object
                properties:
                  price:
                    type: number
                    description: The market price (between 0 and 1)
                    example: 0.999
                  at_time:
                    type: integer
                    description: >-
                      The timestamp for which the price was fetched (Unix
                      timestamp in seconds)
                    example: 1762164600
                required:
                  - price
                  - at_time
              examples:
                with_at_time:
                  summary: Historical price lookup
                  description: Response when `at_time` parameter is provided
                  value:
                    price: 0.999
                    at_time: 1762164600
                real_time:
                  summary: Real-time price lookup
                  description: >-
                    Response when `at_time` parameter is omitted (most recent
                    price)
                  value:
                    price: 0.215
                    at_time: 1757008834
        '400':
          description: Bad Request - Invalid parameters
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Invalid token_id
                  message:
                    type: string
                    example: token_id must be a valid string
        '404':
          description: Not Found - Market not found
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Not found
                  message:
                    type: string
                    example: Market with the provided token_id not found

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt