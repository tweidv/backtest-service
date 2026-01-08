# Markets

> Find markets on Kalshi using various filters including market ticker, event ticker, status, and volume



## OpenAPI

````yaml api-reference/openapi.json get /kalshi/markets
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /kalshi/markets:
    get:
      summary: Get Kalshi Markets
      description: >-
        Fetches Kalshi market data with optional filtering by market ticker,
        event ticker, status, and volume. Returns markets with details including
        pricing, volume, and status information.
      operationId: getKalshiMarkets
      parameters:
        - name: market_ticker
          in: query
          required: false
          description: Filter markets by market ticker(s). Can provide multiple values.
          schema:
            type: array
            items:
              type: string
            example:
              - KXMAYORNYCPARTY-25-D
          style: form
          explode: true
        - name: event_ticker
          in: query
          required: false
          description: Filter markets by event ticker(s). Can provide multiple values.
          schema:
            type: array
            items:
              type: string
            example:
              - KXMAYORNYCPARTY-25
          style: form
          explode: true
        - name: search
          in: query
          required: false
          description: >-
            Search markets by keywords in title and description. Must be URL
            encoded (e.g., 'bitcoin%20price' for 'bitcoin price').
          schema:
            type: string
            example: bitcoin
        - name: status
          in: query
          required: false
          description: Filter markets by status (whether they're open or closed)
          schema:
            type: string
            enum:
              - open
              - closed
            example: open
        - name: min_volume
          in: query
          required: false
          description: >-
            Filter markets with total trading volume greater than or equal to
            this amount (in dollars)
          schema:
            type: number
            example: 10000000
        - name: limit
          in: query
          required: false
          description: 'Number of markets to return (1-100). Default: 10.'
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 10
            example: 20
        - name: offset
          in: query
          required: false
          description: Number of markets to skip for pagination
          schema:
            type: integer
            minimum: 0
            default: 0
            example: 0
      responses:
        '200':
          description: Kalshi markets response with pagination
          content:
            application/json:
              schema:
                type: object
                properties:
                  markets:
                    type: array
                    items:
                      type: object
                      properties:
                        event_ticker:
                          type: string
                          description: The Kalshi event ticker
                          example: KXMAYORNYCPARTY-25
                        market_ticker:
                          type: string
                          description: The Kalshi market ticker
                          example: KXMAYORNYCPARTY-25-D
                        title:
                          type: string
                          description: Market question/title
                          example: >-
                            Will a representative of the Democratic party win
                            the NYC Mayor race in 2025?
                        start_time:
                          type: integer
                          description: Unix timestamp in seconds when the market opens
                          example: 1731150000
                        end_time:
                          type: integer
                          description: >-
                            Unix timestamp in seconds when the market is
                            scheduled to end
                          example: 1793775600
                        close_time:
                          type: integer
                          nullable: true
                          description: >-
                            Unix timestamp in seconds when the market actually
                            resolves/closes (may be before end_time if market
                            finishes early, null if not yet closed)
                          example: 1793775600
                        status:
                          type: string
                          description: Market status
                          enum:
                            - open
                            - closed
                          example: open
                        last_price:
                          type: number
                          description: Last traded price in cents
                          example: 89
                        volume:
                          type: number
                          description: Total trading volume in dollars
                          example: 18261146
                        volume_24h:
                          type: number
                          description: 24-hour trading volume in dollars
                          example: 931138
                        result:
                          type: string
                          nullable: true
                          description: Market result (null if unresolved)
                          example: null
                  pagination:
                    type: object
                    properties:
                      limit:
                        type: integer
                        example: 20
                      offset:
                        type: integer
                        example: 0
                      total:
                        type: integer
                        description: Total number of markets matching the filters
                        example: 150
                      has_more:
                        type: boolean
                        description: Whether there are more markets available
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
                    example: Invalid limit parameter
                  message:
                    type: string
                    example: limit must be a number between 1 and 100

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt