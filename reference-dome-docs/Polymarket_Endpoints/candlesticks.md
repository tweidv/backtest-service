# Candlesticks

> Fetches historical candlestick data for a market identified by `condition_id`, over a specified interval.



## OpenAPI

````yaml api-reference/openapi.json get /polymarket/candlesticks/{condition_id}
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /polymarket/candlesticks/{condition_id}:
    parameters:
      - name: condition_id
        in: path
        required: true
        schema:
          type: string
    get:
      summary: Get Candlesticks
      description: >-
        Fetches historical candlestick data for a market identified by
        `condition_id`, over a specified interval.
      operationId: getCandlesticks
      parameters:
        - name: start_time
          in: query
          required: true
          description: Unix timestamp (in seconds) for start of time range
          schema:
            type: integer
            example: 1640995200
        - name: end_time
          in: query
          required: true
          description: Unix timestamp (in seconds) for end of time range
          schema:
            type: integer
            example: 1672531200
        - name: interval
          in: query
          required: false
          description: |+
            Interval length: 1 = 1m, 60 = 1h, 1440 = 1d. Defaults to 1m. 

            ⚠️ **Note:** There are range limits for `interval` — specifically:
            - `1` (1m): max range **1 week**
            - `60` (1h): max range **1 month**
            - `1440` (1d): max range **1 year**

          schema:
            type: integer
            enum:
              - 1
              - 60
              - 1440
            default: 1
      responses:
        '200':
          description: Candlestick response
          content:
            application/json:
              schema:
                type: object
                properties:
                  candlesticks:
                    type: array
                    description: >-
                      Array of market candlestick data, where each element is a
                      tuple containing candlestick data array and token metadata
                    items:
                      type: array
                      description: Tuple of [candlestick_data_array, token_metadata]
                      minItems: 2
                      maxItems: 2
                      items:
                        oneOf:
                          - type: array
                            description: Candlestick data array
                            items:
                              type: object
                          - type: object
                            description: Token metadata
                            properties:
                              token_id:
                                type: string
                      example:
                        - - end_period_ts: 1727827200
                            open_interest: 8456498
                            price:
                              open: 0
                              high: 0
                              low: 0
                              close: 0
                              open_dollars: '0.0049'
                              high_dollars: '0.0049'
                              low_dollars: '0.0048'
                              close_dollars: '0.0048'
                              mean: 0
                              mean_dollars: '0.0049'
                              previous: 0
                              previous_dollars: '0.0049'
                            volume: 8456498
                            yes_ask:
                              open: 0.00489
                              close: 0.0048200000000000005
                              high: 0.00491
                              low: 0.0048
                              open_dollars: '0.0049'
                              close_dollars: '0.0048'
                              high_dollars: '0.0049'
                              low_dollars: '0.0048'
                            yes_bid:
                              open: 0.00489
                              close: 0.004829999990880811
                              high: 0.004910000000138527
                              low: 0.0048
                              open_dollars: '0.0049'
                              close_dollars: '0.0048'
                              high_dollars: '0.0049'
                              low_dollars: '0.0048'
                        - token_id: >-
                            21742633143463906290569050155826241533067272736897614950488156847949938836455
        '400':
          description: Bad Request - Invalid parameters
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Missing required query parameters
                  required:
                    type: string
                    example: start_time, end_time

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt