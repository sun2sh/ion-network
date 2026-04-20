# ion-core/payment/v1

Indonesian payment method objects and PaymentDeclaration wrapper.

## Attaches to
`beckn:Settlement.settlementAttributes`

## Payment types
| Object | Description |
|---|---|
| QRIS | Quick Response Code Indonesian Standard (static or dynamic) |
| VirtualAccount | Bank virtual account (BCA, BRI, Mandiri, BNI, etc.) |
| EWallet | OVO, DANA, GoPay, LinkAja, ShopeePay, AstraPay, Sakuku |
| CashOnDelivery | COD with collection amount and change instructions |
| BankTransfer | Direct bank transfer |
| BISettlement | BI-FAST / RTGS / SKN interbank settlement |
| BNPL | Buy Now Pay Later (Kredivo, Akulaku, etc.) |
| CardPayment | Credit/debit card (Visa, Mastercard, JCB, UnionPay) |

## PaymentDeclaration
Wraps the specific payment instrument with transaction-level context:
`method`, `collectedBy`, `timing`, `status`, `amount`, `paidAt`, `gatewayRef`, `methodDetail`
