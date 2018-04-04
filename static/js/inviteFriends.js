$(function() {

$('#invite_friends').on('submit', function(e) {
    console.log("INvite Freinds called")
    e.preventDefault();
    $.ajax({
        type: "POST",
        url: "/invite_friends",
        data: $('form.search-form').serialize(),
        success: function(response) {
            console.log("Added")
            $('#friend_email').val('');

        },
        error: function() {
            console.log("Error inviting friends");
        }

    });
    return false;
});
});
