/* Мобильное меню */
$('#mobile_logo, #overlay').click(function() {
	$('.sidebar').toggleClass('open')
	$('.mobile_sidebar .bredcams, .logo_name').toggle()
	$('.sidebar-wrapper').slideToggle();
	$('#overlay').fadeToggle();
})

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


/* Живой поиск */
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

/* Показать архив */
$('#show_archive .form-check-input').click(function() {
	$('.table .archive').fadeToggle();
})