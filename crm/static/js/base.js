/* Мобильное меню */
$('#mobile_logo, #overlay').click(function() {
    $('#mobile_logo .open_b, #mobile_logo .close_b').toggle();
	$('.sidebar').toggleClass('open');
	$('.mobile_sidebar .bredcams, .logo_name').toggle();
	$('.sidebar-wrapper').slideToggle();
	$('#overlay').fadeToggle();
});

/* Показать «Вспомнить пароль» */
$('#recall_password , #recall_password_back').click(function() {
	$('#form_sing-in , #form_recall').toggle('slow');
});

/* Отступ для подвала сайдбара */
var nav_bottom_height = $('.nav .bottom').height() + 20;
$('.nav .top').attr('style','padding-bottom:'+nav_bottom_height+'px;');



/* Новые занятия */
$('.day input:checkbox:checked > :not([type=checkbox])').prop('disabled',true);
$('.day :checkbox').click(function(){
    $(this).parents('.day')
        .find(':not([type=checkbox])')
        .prop('disabled', !this.checked);
});
$('.day:not(:first-child)').append( "<div class=greylineV></div>" );


/* Для кнопки отметить */
$('.workout_page .fio_name').each(function() {
    var fio_name_a = $(this).attr('href');
    $(this).parents('.workout_page tr').find('td').not('td:nth-child(9),td:nth-child(10)').on('click',function() {
        window.location = fio_name_a;
    })
    $(this).parents('.workout_page tr').find('td:nth-child(9)').on('click',function() {
        window.location = $(this).find('a').attr('href');;
    })
})
$('.students_page .fio_name').each(function() {
    var fio_name_a = $(this).attr('href');
    $(this).parents('.students_page tr').find('td').on('click',function() {
        window.location = fio_name_a;
    })
})
$('.sell').each(function() {
    $(this).parents('tr td:nth-child(3)').on('click',function() {
        window.location = $(this).find('a').attr('href');
    })
})
$('.report_page tr').each(function() {
    $(this).on('click',function() {
        window.location = $(this).find('a').attr('href');
    })
})
function buttons_middle () {
    $('.info_for_button').each(function() {
        var ifb_height = $(this).height();
        var fio_name_height = $(this).parents('tr').find('.fio_name').height() + 4;
        var ifb_height_s = $(this).parents('tr').find('.info_for_button_s').height();

        if (ifb_height_s == '0') {
            if (ifb_height < '40') {var ifb_height = 40};
            $(this).parents('tr').find('.btn_box:first-child').attr('style','height:'+ifb_height+'px; margin-top:'+fio_name_height+'px;');
            $(this).parents('tr').find('.btn_box').not('.btn_box:first-child').attr('style','height:'+ifb_height+'px;');
        } else {
            if (ifb_height_s < '40') {var ifb_height_s = 40};
            $(this).parents('tr').find('.btn_box').attr('style','height:'+ifb_height_s+'px;');
        }
    })
}
buttons_middle ()
$('#pills-tab a').on('shown.bs.tab',buttons_middle)

/* Живой поиск */
$('#table_live_search').on('keyup', function() {
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

$('div.btn_box a.btn').click(function(event) {
    let $target = $(event.currentTarget);
    if ($target.attr('pressed')) {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
    $target.find('span').first().addClass('wait');
    $target.attr('pressed', 1);
});

$('div.save_buttons button#add, div.save_buttons button#add-with-autoextend').click(function(event) {
    let $target = $(event.currentTarget);
    if ($target.attr('pressed')) {
        event.preventDefault();
        event.stopPropagation();
        return;
    }
    $target.attr('pressed', 1);
});
