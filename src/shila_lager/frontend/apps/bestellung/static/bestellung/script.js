/**
 * Calculate the order quantity and price for a given input element.
 * @param grihed_id {string} The id of the grihed.
 * @param pricePerCrate {number} The price per crate.
 * @param shouldBeInStock {number} The ideal stock level.
 * @param calculateOrderQuantity {boolean} Whether to calculate the order quantity or use the input value.
 */
function calculateOrder(grihed_id, pricePerCrate, shouldBeInStock, calculateOrderQuantity) {
    const currentStockInput = document.querySelector(`input[name="current_stock_${grihed_id}"]`)
    const orderQuantityInput = document.querySelector(`input[name="order_qty_${grihed_id}"]`);

    const orderPriceDisplay = document.querySelector(`td[id="price_${grihed_id}"]`);
    const stockPriceDisplay = document.querySelector(`td[id="stock_value_${grihed_id}"]`);

    const currentStock = parseInt(currentStockInput.value) || 0;
    const orderQuantity = calculateOrderQuantity ? Math.max(0, shouldBeInStock - currentStock) : parseInt(orderQuantityInput.value);

    orderQuantityInput.value = orderQuantity;
    orderPriceDisplay.innerText = `$${(orderQuantity * pricePerCrate).toFixed(2)}`;
    stockPriceDisplay.innerText = `$${(currentStock * pricePerCrate).toFixed(2)}`;
}
