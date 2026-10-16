# Commerce

The system supports a single merchant selling physical goods to registered customers across multiple countries, currencies, and languages.

## Language

**Merchant**:
The single business that owns the catalog, inventory, and customer sales in this system.
_Avoid_: Seller, vendor, shop owner

**Customer**:
A registered person who can place and review orders.
_Avoid_: Buyer, client, guest

**Product**:
A physical good offered by the Merchant for sale.
_Avoid_: Item, merchandise

**Variant**:
A purchasable version of a Product defined by attributes such as color or size. SKU, weight, price, and inventory are tracked at this level.
_Avoid_: Product option, item

**Brand**:
The commercial identity associated with a Product; multiple Brands may appear in the Merchant's catalog without becoming sellers.
_Avoid_: Merchant, Seller, Vendor

**Warehouse**:
A physical location where inventory for Variants is held and fulfilled.
_Avoid_: Stockroom, inventory location

**Storefront**:
The public API surface a Customer browses and buys through, serving only published catalog content at prices resolved into their Transaction Currency; distinct from the Admin API, which the Merchant's internal operators work through.
_Avoid_: Shop, frontend, public API, client

**Supported Country**:
A country where the Merchant accepts orders, with defined currencies, languages, taxes, shipping methods, and payment methods.
_Avoid_: Market, region

**Order**:
A Customer's confirmed purchase whose products, prices, exchange rate, taxes, shipping charge, discounts, and delivery address preserve the terms agreed at checkout.
_Avoid_: Cart, transaction

**Order Line**:
A preserved Product Variant, quantity, and monetary breakdown within an Order.
_Avoid_: Cart item, product row

**Payment Attempt**:
One attempt to collect money for an Order through a Payment Method; an Order may have multiple attempts without increasing the amount owed.
_Avoid_: Payment, transaction

**Shipment**:
A separately trackable delivery containing quantities from one or more Order Lines.
_Avoid_: Order, fulfillment, parcel

**Inventory Reservation**:
A temporary claim on a Variant's stock at a Warehouse while a Customer completes checkout.
_Avoid_: Stock deduction, hold

**Inventory Movement**:
An immutable record explaining a stock increase, decrease, reservation release, return, or manual correction at a Warehouse.
_Avoid_: Stock edit, inventory log

**Cash on Delivery**:
A payment method in which the Customer pays when the shipment is delivered.
_Avoid_: Offline payment, cash payment

**Transaction Currency**:
The supported currency selected by the Customer and locked on an Order for display, payment, refund, and accounting of that purchase.
_Avoid_: Local currency, display currency

**Exchange Rate**:
The externally sourced conversion rate used to derive a Transaction Currency amount from the Merchant's base price and then locked on the Order.
_Avoid_: Live price, AI rate

**Base Price**:
The Merchant-defined VND price of a Variant from which supported Transaction Currency amounts are derived.
_Avoid_: Local price, converted price

**Wishlist**:
A Customer's single saved collection of Products they may want to purchase later.
_Avoid_: Favorites, saved cart

**Cart**:
A Customer's mutable selection of Product Variants before checkout; its prices, discounts, and currency are provisional and may be recalculated.
_Avoid_: Order, Wishlist

**Promotion**:
A configured pricing benefit automatically applied when its conditions are satisfied.
_Avoid_: Coupon, Gift Card

**Coupon**:
A Customer-entered code that activates one eligible promotional benefit on an Order.
_Avoid_: Promotion, Gift Card, voucher

**Review**:
A moderated rating and comment a Customer may submit for a Product after receiving it in a completed Order.
_Avoid_: Feedback, testimonial

**Gift Card**:
A currency-specific stored-value payment instrument whose balance can be spent across multiple Orders.
_Avoid_: Coupon, voucher, discount code

**Gift Card Ledger**:
The immutable history of Gift Card issuance, activation, spending, refunding, expiry, and staff adjustments.
_Avoid_: Balance history, audit log

**Return Request**:
A Customer's request to send back one or more Order Lines for review before a refund or replacement is approved.
_Avoid_: Cancellation, refund request

**Refund**:
A full or partial reversal of money paid for accepted returned goods or another approved adjustment.
_Avoid_: Return, cancellation

**Shipping Method**:
A delivery option available for an Order's destination, with an agreed charge and service level locked at checkout.
_Avoid_: Carrier, delivery fee

**Catalog Translation**:
A locale-specific version of Product content that must be approved before publication; AI-generated text is treated only as a draft.
_Avoid_: Automatic translation, locale copy

**Master Admin**:
An internal operator with unrestricted authority over the commerce system and other staff accounts.
_Avoid_: Superuser, owner

**Store Manager**:
An internal operator who manages the catalog, pricing, inventory, promotions, and orders but cannot manage Master Admin accounts, security settings, or sensitive integrations.
_Avoid_: Manager, admin

**Order Staff**:
An internal operator responsible for processing and updating customer orders.
_Avoid_: Shipper, operator
