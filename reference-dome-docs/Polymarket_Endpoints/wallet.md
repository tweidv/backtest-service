# Wallet

> Fetches wallet information by providing either an EOA (Externally Owned Account) address or a proxy wallet address. Returns the associated EOA, proxy, and wallet type. Optionally returns trading metrics including total volume, number of trades, and unique markets traded when `with_metrics=true`.



## OpenAPI

````yaml api-reference/openapi.json get /polymarket/wallet
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /polymarket/wallet:
    get:
      summary: Get Wallet
      description: >-
        Fetches wallet information by providing either an EOA (Externally Owned
        Account) address or a proxy wallet address. Returns the associated EOA,
        proxy, and wallet type information. Optionally returns trading metrics
        when `with_metrics=true`.
      operationId: getWallet
      parameters:
        - name: eoa
          in: query
          required: false
          description: >-
            EOA (Externally Owned Account) wallet address. Either `eoa` or
            `proxy` must be provided, but not both.
          schema:
            type: string
            pattern: ^0x[0-9a-fA-F]{40}$
            example: '0xe9a69b28ffd86f6ea0c5d8171c95537479b84a29'
        - name: proxy
          in: query
          required: false
          description: >-
            Proxy wallet address. Either `eoa` or `proxy` must be provided, but
            not both.
          schema:
            type: string
            pattern: ^0x[0-9a-fA-F]{40}$
            example: '0x60881d7dce725bfb0399ee0b11cc11f5782f257d'
        - name: with_metrics
          in: query
          required: false
          description: >-
            Whether to include wallet trading metrics (total volume, trades, and
            markets). Pass `true` to include metrics. Metrics are computed only
            when explicitly requested for performance reasons.
          schema:
            type: string
            enum:
              - 'true'
              - 'false'
            example: 'true'
        - name: start_time
          in: query
          required: false
          description: >-
            Optional start date for metrics calculation (Unix timestamp in
            seconds). Only used when `with_metrics=true`.
          schema:
            type: integer
            example: 1640995200
        - name: end_time
          in: query
          required: false
          description: >-
            Optional end date for metrics calculation (Unix timestamp in
            seconds). Only used when `with_metrics=true`.
          schema:
            type: integer
            example: 1672531200
      responses:
        '200':
          description: Wallet information response
          content:
            application/json:
              schema:
                type: object
                properties:
                  eoa:
                    type: string
                    description: The EOA (Externally Owned Account) wallet address
                    example: '0xe9a69b28ffd86f6ea0c5d8171c95537479b84a29'
                  proxy:
                    type: string
                    description: The proxy wallet address
                    example: '0x60881d7dce725bfb0399ee0b11cc11f5782f257d'
                  wallet_type:
                    type: string
                    description: The type of wallet
                    example: safe
                  wallet_metrics:
                    type: object
                    description: >-
                      Trading metrics for this wallet (only present when
                      with_metrics=true)
                    properties:
                      total_volume:
                        type: number
                        description: Total trading volume in USD
                        example: 150000.5
                      total_trades:
                        type: number
                        description: >-
                          Total number of trades (orders where this wallet was
                          the maker)
                        example: 450
                      total_markets:
                        type: number
                        description: Total number of unique markets traded in
                        example: 25
                      highest_volume_day:
                        type: object
                        description: The day with the highest number of shares traded
                        properties:
                          date:
                            type: string
                            format: date
                            description: Date in YYYY-MM-DD format
                            example: '2025-10-12'
                          volume:
                            type: number
                            description: >-
                              Total shares traded on that day (normalized,
                              divided by 1,000,000)
                            example: 25000.75
                          trades:
                            type: number
                            description: Number of trades executed on that day
                            example: 145
                        required:
                          - date
                          - volume
                          - trades
                      merges:
                        type: number
                        description: Total number of token merges performed by this wallet
                        example: 262
                      splits:
                        type: number
                        description: Total number of token splits performed by this wallet
                        example: 31
                      conversions:
                        type: number
                        description: >-
                          Total number of token conversions performed by this
                          wallet
                        example: 4
                      redemptions:
                        type: number
                        description: >-
                          Total number of token redemptions performed by this
                          wallet
                        example: 2338
                required:
                  - eoa
                  - proxy
                  - wallet_type
              examples:
                without_metrics:
                  summary: Basic wallet information
                  description: Response when with_metrics is not provided or false
                  value:
                    eoa: '0xe9a69b28ffd86f6ea0c5d8171c95537479b84a29'
                    proxy: '0x60881d7dce725bfb0399ee0b11cc11f5782f257d'
                    wallet_type: safe
                with_metrics:
                  summary: Wallet information with metrics
                  description: Response when with_metrics=true
                  value:
                    eoa: '0xe9a69b28ffd86f6ea0c5d8171c95537479b84a29'
                    proxy: '0x60881d7dce725bfb0399ee0b11cc11f5782f257d'
                    wallet_type: safe
                    wallet_metrics:
                      total_volume: 150000.5
                      total_trades: 450
                      total_markets: 25
                      highest_volume_day:
                        date: '2025-10-12'
                        volume: 25000.75
                        trades: 145
        '400':
          description: Bad Request - Invalid or missing parameters
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: BAD_REQUEST
                  message:
                    type: string
                    example: >-
                      Either eoa or proxy parameter must be provided, but not
                      both
              examples:
                missing_parameter:
                  summary: Missing required parameter
                  value:
                    error: BAD_REQUEST
                    message: Either eoa or proxy parameter must be provided
                both_parameters:
                  summary: Both parameters provided
                  value:
                    error: BAD_REQUEST
                    message: Only one of eoa or proxy can be provided, not both
                invalid_address:
                  summary: Invalid wallet address format
                  value:
                    error: BAD_REQUEST
                    message: Invalid wallet address format
        '404':
          description: Not Found - Wallet not found
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: NOT_FOUND
                  message:
                    type: string
                    example: Wallet not found

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt