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

    $('.todo-checkbox').click(function() {
        var data = {
            'checked': $(this).is(':checked'),
            'value': $(this).parent().text(),
            'protocol': $(this).data('protocol'),
            'id': $(this).data('id')
        };
        $.postJSON('/__manage/todo', data, function(response) {
            console.log(response);
        });
    });
});
