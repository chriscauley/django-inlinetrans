

(function ($) {
    String.format = String.format || function(format){
        var args = Array.prototype.slice.call(arguments, 1);

        return format.replace(/\{(\d+)\}/g, function(m, i) {
            return args[i];
        });
    };

    $.fn.inlinetranstoolbar = function(toolbar_tpl, new_translation_url, restart_url, messages_dict) {
        return this.each(function() {
            $(this).html(toolbar_tpl);
            var some_changes = false;
            
            var do_ajax = function(item, msgid, msgstr, retry) {
                active_loading();
                var jsondata = $.param({msgid:msgid, msgstr:msgstr, retry:retry});

                $.ajax({
                    data: jsondata,
                    url: new_translation_url,
                    type: "POST",
                    headers: {"X-CSRFToken": $.cookie('csrftoken')},
                    async: true,
                    dataType: "json",
                    success: function(response){
                        if (!response.errors) {
                            if (retry) {
                               alert(response.message);
                            }

                            item.html(msgstr || msgid);
                            some_changes = true;
                            disable_loading();
                            active_restart();

                        } else if (!response.question) {  // Critical error
                            alert(response.message);
                            disable_loading();

                        } else {  // Allowed to retry
                            if (confirm(response.message + '\n\n' + response.question)) {
                                do_ajax(item, msgid, msgstr, true);
                            } else {
                                disable_loading();
                            }
                        }
                    },
                    error: function(response){
                        alert(messages_dict.error_cant_send);
                        disable_loading();
                    }
                });
            }
 
            var send_translation = function () {
                var msgid = $(this).attr('rel');
                var untranslated = false;
                var old_msgstr = $(this).html() ;
                var msgstr = prompt(String.format(messages_dict.givetranslationfor, msgid), old_msgstr);

                if (msgstr == null){
                    return false;
                }

                if (msgstr == ""){
                    answer = confirm(messages_dict.emptytranslation);
                    var msgstr = "";

                } else {
                    answer = true;
                }

                if(answer){
                    var item = $(this);
                    do_ajax(item, msgid, msgstr, false);
                }

                return false;
            }

            var active_translation = false;

            var active_translations = function () {
                if ($(".inlinetrans-actions .active").length && !active_translation) {
                    active_translation = true;

                    $("a > .translatable").each(function(){
                        $(this).parent().click(function () {
                            return false;
                        });
                    });

                    $(".translatable").click(send_translation);
                }
            }

            var active_loading = function() {
                $(".inlinetrans-busy").show();
            }

            var disable_loading = function() {
                $(".inlinetrans-busy").hide();
            }

            var disable_translations = function () {
                if ($(".inlinetrans-actions .active").length == 0 && active_translation) {
                    active_translation = false;
                    $(".translatable").unbind("click", send_translation);

                    $("a > .translatable").each(function(){
                        $(this).parent().unbind('click');
                    });
                }
            }

            $(".highlight-trans").click(function () {
                $(".translatable").toggleClass("inlinetrans-highlight");
                $(this).toggleClass("active");

                if ($(this).hasClass("active")) {
                    active_translations();
                } else {
                    disable_translations();
                }
            });

            $(".highlight-notrans").click(function(){
                $(this).toggleClass("active");

                if ($(this).hasClass("active")) {
                    active_translations();
                } else {
                    disable_translations();
                }

                $(".untranslated").toggleClass("inlinetrans-untranslated");
            });

            active_restart = function () {
                $(".restart-server").css({display: 'inline'});

                $(".restart-server").click(function(){
                    if (some_changes){
                        $(".restart-server").html(messages_dict.applying_changes);
                        $(this).toggleClass("active");
                        active_loading();

                        $.ajax({
                                data: {restart: 1},
                                url: restart_url,
                                type: "POST",
                                headers: { "X-CSRFToken": $.cookie('csrftoken') },
                                async: true,
                                success: function(response){
                                    some_changes = false;
                                    $(".restart-server").html(messages_dict.reloading);

                                    setTimeout(function(){
                                        document.location = document.location;
                                        $(".restart-server").html(messages_dict.apply_changes);
                                        $(".restart-server").toggleClass("active");
                                        disable_loading();
                                    }, parseInt(response) * 1000);
                                },
                                error: function(response){
                                    alert(messages_dict.error_cant_restart);
                                    disable_loading();
                                }
                        });
                    }
                });
            }
        });
    };
})(jQuery);
