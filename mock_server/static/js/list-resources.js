$(function(){

    // make code pretty
    window.prettyPrint && prettyPrint();

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
