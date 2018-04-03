
$( document ).ready( function() {
        $.ajax({
        type: 'GET',
    url: '/user/info',
    success: function(result) {
            console.log(result)
        $("#profImage").attr('src', result['image_url']);
        $("#profImage1").attr('src',  result['image_url']);
        $("#rightProfImage").attr('src', result['image_url']);
        $("#rightProfImage1").attr('src',  result['image_url']);
        $("#userName").text(result['name']);
        $("#userHiddenName").text(result['name']);
        if (!!result['email']) {
            $.cookie('pop', '20000');
        }


    }
});
    } );