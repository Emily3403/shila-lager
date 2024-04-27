/**
 * Calculate the order quantity and price for a given input element.
 * @param grihed_id {string} The id of the grihed.
 * @param pricePerCrate {number} The price per crate.
 * @param shouldBeInStock {number} The ideal stock level.
 */
function calculateOrder(grihed_id, pricePerCrate, shouldBeInStock) {
    const currentStockInput = document.querySelector(`input[name="current_stock_${grihed_id}"]`)
    const extraOrderInput = document.querySelector(`input[name="extra_order_qty_${grihed_id}"]`);
    const orderQuantityDisplay = document.querySelector(`td[id="order_qty_${grihed_id}"]`);
    const orderPriceDisplay = document.querySelector(`td[id="price_${grihed_id}"]`);

    const currentStock = parseInt(currentStockInput.value) || 0;
    const extraStock = parseInt(extraOrderInput.value) || 0;
    const orderQuantity = Math.max(0, shouldBeInStock - currentStock + extraStock)

    orderQuantityDisplay.innerText = orderQuantity;
    orderPriceDisplay.innerText = `${(orderQuantity * pricePerCrate).toFixed(2)}€`;
}

document.addEventListener('DOMContentLoaded', () => {
    const grihedForm = document.querySelector('form[id="grihed_form"]');

    // Submit changes to the form every time the user changes the input.
    grihedForm.addEventListener('input', (event) => {
        const input = event.target;
        console.log(input.attributes)
    });
});
