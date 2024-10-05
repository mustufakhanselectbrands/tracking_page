
$("#orderForm").on("submit", function (event) {
    event.preventDefault();
    var ref_no = $("#ref_no").val();
    var contact_no = $("#contact_no").val();

    $.ajax({
        type: "POST",
        url: "order/", 
        data: JSON.stringify({
            ref_no: ref_no,
            contact_no: contact_no
        }),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            if (data.message === "Order Details Validate") {
                alert("Order Details Validate");
            } else {
                alert("Something went wrong. Please try again.");
            }
        },
        error: function () {
            alert("An error occurred. Please try again.");
        }
    });
});
