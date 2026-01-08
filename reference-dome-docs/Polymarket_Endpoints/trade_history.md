# Trade History

> Fetches historical trade data with optional filtering by market, condition, token, time range, and user's wallet address.



## OpenAPI

````yaml api-reference/openapi.json get /polymarket/orders
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /polymarket/orders:
    get:
      summary: Get Orders
      description: >-
        Fetches order data with optional filtering by market, condition, token,
        time range, and user. Returns orders that match either primary or
        secondary token IDs for markets. If no filters provided, fetches the
        latest trades happening in real-time. Only one of market_slug, token_id,
        or condition_id can be provided.
      operationId: getOrders
      parameters:
        - name: market_slug
          in: query
          required: false
          description: Filter orders by market slug
          schema:
            type: string
            example: bitcoin-up-or-down-july-25-8pm-et
        - name: condition_id
          in: query
          required: false
          description: Filter orders by condition ID
          schema:
            type: string
            example: '0x4567b275e6b667a6217f5cb4f06a797d3a1eaf1d0281fb5bc8c75e2046ae7e57'
        - name: token_id
          in: query
          required: false
          description: Filter orders by token ID
          schema:
            type: string
            example: >-
              58519484510520807142687824915233722607092670035910114837910294451210534222702
        - name: start_time
          in: query
          required: false
          description: Filter orders from this Unix timestamp in seconds (inclusive)
          schema:
            type: integer
            example: 1640995200
        - name: end_time
          in: query
          required: false
          description: Filter orders until this Unix timestamp in seconds (inclusive)
          schema:
            type: integer
            example: 1672531200
        - name: limit
          in: query
          required: false
          description: Number of orders to return (1-1000)
          schema:
            type: integer
            minimum: 1
            maximum: 1000
            default: 100
            example: 50
        - name: offset
          in: query
          required: false
          description: Number of orders to skip for pagination
          schema:
            type: integer
            minimum: 0
            default: 0
            example: 0
        - name: user
          in: query
          required: false
          description: Filter orders by user (wallet address)
          schema:
            type: string
            example: '0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b'
      responses:
        '200':
          description: Orders response with pagination
          content:
            application/json:
              schema:
                type: object
                properties:
                  orders:
                    type: array
                    items:
                      type: object
                      properties:
                        token_id:
                          type: string
                          example: >-
                            58519484510520807142687824915233722607092670035910114837910294451210534222702
                        token_label:
                          type: string
                          description: Human readable label for this outcome (yes/no etc)
                          example: 'Yes'
                        side:
                          type: string
                          enum:
                            - BUY
                            - SELL
                          example: BUY
                        market_slug:
                          type: string
                          example: bitcoin-up-or-down-july-25-8pm-et
                        condition_id:
                          type: string
                          example: >-
                            0x4567b275e6b667a6217f5cb4f06a797d3a1eaf1d0281fb5bc8c75e2046ae7e57
                        shares:
                          type: number
                          description: Raw number of shares purchased (from the blockchain)
                          example: 4995000
                        shares_normalized:
                          type: number
                          description: >-
                            Number of shares purchased normalized (this is raw
                            divided by 1000000)
                          example: 4.995
                        price:
                          type: number
                          description: Price per share
                          example: 0.65
                        tx_hash:
                          type: string
                          description: Transaction hash of the order
                          example: >-
                            0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12
                        title:
                          type: string
                          description: Market title
                          example: >-
                            Will Bitcoin be above $50,000 on July 25, 2025 at
                            8:00 PM ET?
                        timestamp:
                          type: integer
                          description: Unix timestamp in seconds when the order was placed
                          example: 1757008834
                        order_hash:
                          type: string
                          description: Hash of the order
                          example: >-
                            0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
                        user:
                          type: string
                          description: Maker address of the order
                          example: '0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b'
                        taker:
                          type: string
                          description: >-
                            Taker address that was part of this trade. Note:
                            This can often be the CTF exchange and is not always
                            the true taker, proceed with caution using taker
                            information
                          example: '0x8d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e'
                  pagination:
                    type: object
                    properties:
                      limit:
                        type: integer
                        example: 50
                      offset:
                        type: integer
                        example: 0
                      total:
                        type: integer
                        description: Total number of orders matching the filters
                        example: 1250
                      has_more:
                        type: boolean
                        description: Whether there are more orders available
                        example: true
        '400':
          description: Bad Request - Invalid parameters or validation errors
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Invalid start_time parameter
                  message:
                    type: string
                    example: start_time must be a valid Unix timestamp
              examples:
                invalid_timestamp:
                  summary: Invalid timestamp
                  value:
                    error: Invalid start_time parameter
                    message: start_time must be a valid Unix timestamp
                invalid_time_range:
                  summary: Invalid time range
                  value:
                    error: Invalid time range
                    message: start_time must be less than end_time
                invalid_limit:
                  summary: Invalid limit
                  value:
                    error: Invalid limit parameter
                    message: limit must be a number between 1 and 1000
                invalid_offset:
                  summary: Invalid offset
                  value:
                    error: Invalid offset parameter
                    message: offset must be a non-negative number
                missing_required_filter:
                  summary: Missing required filter
                  value:
                    error: Missing required filter parameter
                    message: >-
                      At least one of market_slug, condition_id, user, or
                      token_id must be provided
                invalid_filter_combination:
                  summary: Invalid filter combination
                  value:
                    error: Invalid filter combination
                    message: >-
                      Only one of market_slug, token_id, or condition_id can be
                      provided

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt