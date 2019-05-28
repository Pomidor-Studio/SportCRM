/* Мобильное меню */
$('#mobile_logo, #overlay').click(function() {
    $('#mobile_logo .open_b, #mobile_logo .close_b').toggle();
	$('.sidebar').toggleClass('open')
	$('.mobile_sidebar .bredcams, .logo_name').toggle()
	$('.sidebar-wrapper').slideToggle();
	$('#overlay').fadeToggle();
});

/* Показать «Вспомнить пароль» */
$('#recall_password , #recall_password_back').click(function() {
	$('#form_sing-in , #form_recall').toggle('slow');
});

/* Отступ для подвала сайдбара */
var nav_bottom_height = $('.nav .bottom').height() + 20
$('.nav .top').attr('style','padding-bottom:'+nav_bottom_height+'px;')



/* Новые занятия */
$('.day input:checkbox:checked > :not([type=checkbox])').prop('disabled',true);
$('.day :checkbox').click(function(){
	if (this.checked) {
		$(this).parents('.day').find(':not([type=checkbox])').prop('disabled',false);
	}
	else{
		$(this).parents('.day').find(':not([type=checkbox])').prop('disabled',true);
	}
});
$('.day:not(:first-child)').append( "<div class=greylineV></div>" );


/* Живой поиск 
$('#table_search').on('keyup', function() {
	var value = $(this).val();
	var patt = new RegExp(value, "i");
	
	$('.table tbody').find('tr').each(function() {
		if (!($(this).find('td').text().search(patt) >= 0)) {
			$(this).not('.myHead').hide();
		}
			if (($(this).find('td').text().search(patt) >= 0)) {
			$(this).show();
		}
	
	});
});
*/

/* Выбор абонемента на занятие 
$('.subscription_select input').click(function() {
	var data = $(this).attr('data-subscription')
	$(this).parents('tr').find('input[data-subscription='+data+']').prop('checked', true)
	$(this).parents('tr').find('.btn-mark, .btn-pay').attr('data-subscription',data)
})
*/

/* Показать архив 
$('#show_archive .form-check-input').click(function() {
	$('.table .archive').fadeToggle();
})
*/

/* Копировать в буфер */
$('.btn-copy').click(function() {
	var copyHref = $(this).next('span').html()
	$(this).next('span').html('Скопировано!')
	$(this).delay(1500).queue(function(next){
	    $(this).next('span').html(copyHref)
	    next();
	});
})
$('#copy_url').click(function() {
	var copyHref = $(this).html()
	$(this).html('Скопировано!').addClass('btn-primary')
	$(this).delay(1500).queue(function(next){
	    $(this).html(copyHref).removeClass('btn-primary')
	    next();
	});
})






/* Абонементы */
$('#no_visit_limit').click(function() {
	$('#id_visit_limit').prop('disabled', function(i, v) { return !v; });
})
$('#subscription_all').change(function() {
    var checkboxes = $(this).closest('.subscription_check').find(':checkbox').not($(this));
    checkboxes.prop('checked', $(this).is(':checked'));
});
$('.subscription_check').find('input:not(#subscription_all)').click(function() {
	$('#subscription_all').prop('checked',false)
})



/* Просмотр ученика */
$('.btn-down, .buy_subscriptions .fio_name').click(function() {
	$(this).parents('tr').toggleClass('active')
	$(this).parents('tr').next('tr').toggleClass('active').toggle();
	$(this).parents('tr').find('.date_end').toggle();
	return(false)
})
$('.buy_subscriptions .cancel').click(function() {
	$(this).parents('tr').prev('tr').toggleClass('active')
	$(this).parents('tr').toggleClass('active').toggle();
	$(this).parents('tr').find('.date_end').toggle();
	return(false)
})
$.urlParam = function(name){
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results==null) {
       return null;
    }
    return decodeURI(results[1]) || 0;
}
var sell = $.urlParam('sell');
if (sell == 'yes') {
	$('.buy_subscriptions .cancel').parents('tr').prev('tr').toggleClass('active')
	$('.buy_subscriptions .cancel').parents('tr').toggleClass('active').toggle();
} 


/* Другая причина в селекте 
$('#id_reason').change(function() {
  var option = $(this).find('option:selected').val();
  if (option == 'Другая') {
	  $('#some_reason').fadeIn();
  } else {
	  $('#some_reason').fadeOut();
  }
});
*/


/* Архивирование ученика */
$('#confirm_popup').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget);
    var url = button.data('url');
    var action_text = button.data('action-text');
    var title = button.data('title');
    var body = button.data('body-text');

    var modal = $(this);
    modal.find('.modal-body h5').text(body);
    modal.find('.modal-title').text(title);
    modal.find('input[type=submit]').attr('value', action_text);
    modal.find('form').attr('action', url);
});
