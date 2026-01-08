# Wallet Profit-and-Loss

> Fetches the **realized** profit and loss (PnL) for a specific wallet address over a specified time range and granularity. **Note:** This will differ to what you see on Polymarket's dashboard since Polymarket showcases historical unrealized PnL. This API tracks realized gains only - from either confirmed sells or redeems. We do not realize a gain/loss until a finished market is redeemed.



## OpenAPI

````yaml api-reference/openapi.json get /polymarket/wallet/pnl/{wallet_address}
openapi: 3.0.3
info:
  title: Dome API
  description: APIs for prediction markets.
  version: 0.0.1
servers:
  - url: https://api.domeapi.io/v1
security: []
paths:
  /polymarket/wallet/pnl/{wallet_address}:
    parameters:
      - name: wallet_address
        in: path
        required: true
        schema:
          type: string
          pattern: ^0x[0-9a-fA-F]{40}$
          example: '0x1234567890abcdef1234567890abcdef12345678'
    get:
      summary: Get Wallet PnL
      description: >-
        Fetches the REALIZED profit and loss (PnL) for a specific wallet address
        over a specified time range and granularity. **Note:** This will differ
        to what you see on Polymarket's dashboard since Polymarket showcases
        historical unrealized PnL. This API tracks realized gains only - from
        either confirmed sells or redeems. We do not realize a gain/loss until a
        finished market is redeemed.
      operationId: getWalletPnl
      parameters:
        - name: granularity
          in: query
          required: true
          schema:
            type: string
            enum:
              - day
              - week
              - month
              - year
              - all
            example: day
        - name: start_time
          in: query
          required: false
          description: Defaults to first day of first trade if not provided.
          schema:
            type: integer
            example: 1726857600
        - name: end_time
          in: query
          required: false
          description: Defaults to the current date if not provided.
          schema:
            type: integer
            example: 1758316829
      responses:
        '200':
          description: PnL response
          content:
            application/json:
              schema:
                type: object
                properties:
                  granularity:
                    type: string
                    example: day
                  start_time:
                    type: integer
                    example: 1726857600
                  end_time:
                    type: integer
                    example: 1758316829
                  wallet_address:
                    type: string
                    example: '0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b'
                  pnl_over_time:
                    type: array
                    items:
                      type: object
                      properties:
                        timestamp:
                          type: integer
                          example: 1726857600
                        pnl_to_date:
                          type: number
                          example: 2001
        '400':
          description: Bad Request
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
                    example: Invalid or missing parameters.
        '503':
          description: Internal Server Error
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: INTERNAL_SERVER_ERROR
                  message:
                    type: string
                    example: Internal Server Error. Dome Admins contacted.

````

---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://docs.domeapi.io/llms.txt