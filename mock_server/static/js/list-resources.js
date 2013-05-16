$(function(){

    // make code pretty
    window.prettyPrint && prettyPrint();

    $('a[data-toggle="tab"]').on('shown', function (e) {
        $('#'+$(this).attr('class')+'-edit').attr('data-format', $(this).html());
    });
    $('.edit-button').click(function() {
        $(this).attr('href', $(this).attr('href')+$(this).attr('data-format'));
    });

    // MENU
    var offset = $('#sidenav').offset();
    var topPadding = 30;

    $(window).scroll(function() {
      if ($(window).scrollTop() > offset.top - topPadding) {
          $('#sidenav').css('top', '0');
          $('#sidenav').css('position', 'fixed');
      } else {
          $('#sidenav').css('position', 'static');
      }
    });

});
