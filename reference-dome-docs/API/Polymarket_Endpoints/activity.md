# Activity

> Fetches activity data for a specific user with optional filtering by market, condition, and time range. Returns trading activity including `MERGES`, `SPLITS`, and `REDEEMS`.



## OpenAPI

````yaml api-reference/openapi.json get /polymarket/activity
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /polymarket/activity:
    get:
      summary: Get Activity
      description: >-
        Fetches activity data for a specific user with optional filtering by
        market, condition, and time range. Returns trading activity including
        `MERGES`, `SPLITS`, and `REDEEMS`.
      operationId: getActivity
      parameters:
        - name: user
          in: query
          required: true
          description: User wallet address to fetch activity for
          schema:
            type: string
            pattern: ^0x[0-9a-fA-F]{40}$
            example: '0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b'
        - name: start_time
          in: query
          required: false
          description: Filter activity from this Unix timestamp in seconds (inclusive)
          schema:
            type: integer
            example: 1640995200
        - name: end_time
          in: query
          required: false
          description: Filter activity until this Unix timestamp in seconds (inclusive)
          schema:
            type: integer
            example: 1672531200
        - name: market_slug
          in: query
          required: false
          description: Filter activity by market slug
          schema:
            type: string
            example: bitcoin-up-or-down-july-25-8pm-et
        - name: condition_id
          in: query
          required: false
          description: Filter activity by condition ID
          schema:
            type: string
            example: '0x4567b275e6b667a6217f5cb4f06a797d3a1eaf1d0281fb5bc8c75e2046ae7e57'
        - name: limit
          in: query
          required: false
          description: Number of activities to return (1-1000)
          schema:
            type: integer
            minimum: 1
            maximum: 1000
            default: 100
            example: 50
        - name: offset
          in: query
          required: false
          description: Number of activities to skip for pagination
          schema:
            type: integer
            minimum: 0
            default: 0
            example: 0
      responses:
        '200':
          description: Activity response with pagination
          content:
            application/json:
              schema:
                type: object
                properties:
                  activities:
                    type: array
                    items:
                      type: object
                      properties:
                        token_id:
                          type: string
                          example: ''
                        side:
                          type: string
                          enum:
                            - MERGE
                            - SPLIT
                            - REDEEM
                          example: REDEEM
                        market_slug:
                          type: string
                          example: will-the-doj-charge-boeing
                        condition_id:
                          type: string
                          example: >-
                            0x92e4b1b8e0621fab0537486e7d527322569d7a8fd394b3098ff4bb1d6e1c0bbd
                        shares:
                          type: number
                          example: 187722726
                          description: Raw number of shares (from the blockchain)
                        shares_normalized:
                          type: number
                          example: 187.722726
                          description: Number of shares normalized (raw divided by 1000000)
                        price:
                          type: number
                          example: 1
                        tx_hash:
                          type: string
                          example: >-
                            0x028baff23a90c10728606781d15077098ee93c991ea204aa52a0bd2869187574
                        title:
                          type: string
                          example: Will the DOJ charge Boeing?
                        timestamp:
                          type: integer
                          description: Unix timestamp in seconds when the activity occurred
                          example: 1721263049
                        order_hash:
                          type: string
                          example: ''
                        user:
                          type: string
                          description: User wallet address
                          example: '0xfd9c3e7f8c56eb4186372f343c873cce154b3873'
                  pagination:
                    type: object
                    properties:
                      limit:
                        type: integer
                        example: 50
                      offset:
                        type: integer
                        example: 0
                      count:
                        type: integer
                        description: Total number of activities matching the filters
                        example: 1250
                      has_more:
                        type: boolean
                        description: Whether there are more activities available
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
                    example: Missing required parameter
                  message:
                    type: string
                    example: user parameter is required
              examples:
                missing_user:
                  summary: Missing required user parameter
                  value:
                    error: Missing required parameter
                    message: user parameter is required
                invalid_start_time:
                  summary: Invalid start_time parameter
                  value:
                    error: Invalid start_time parameter
                    message: start_time must be a valid Unix timestamp
                invalid_end_time:
                  summary: Invalid end_time parameter
                  value:
                    error: Invalid end_time parameter
                    message: end_time must be a valid Unix timestamp
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
                invalid_filter_combination:
                  summary: Invalid filter combination
                  value:
                    error: Invalid filter combination
                    message: Only one of market_slug or condition_id can be provided
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
                    example: Failed to fetch activity data

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt