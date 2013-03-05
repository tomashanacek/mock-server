!function ($) {

  $(function(){

    var $window = $(window)

    // side bar
    setTimeout(function () {
      $('.bs-docs-sidenav').affix({
        offset: {
          top: function () { return $window.width() <= 980 ? 290 : 210 }
        , bottom: 270
        }
      })
    }, 100)

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