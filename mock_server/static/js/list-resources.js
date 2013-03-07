!function ($) {

  $(function(){

    var $window = $(window)

    // make code pretty
    window.prettyPrint && prettyPrint()

  })

}(window.jQuery)

$('a[data-toggle="tab"]').on('shown', function (e) {
    $('#'+$(this).attr('class')+'-edit').attr('data-format', $(this).html())
});
$('.edit-button').click(function() {
    $(this).attr('href', $(this).attr('href')+$(this).attr('data-format'));
});
