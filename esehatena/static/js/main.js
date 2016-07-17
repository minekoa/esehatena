
var addSiteHeader = function() {
   $('#Main').append('<h1 id="site_title" class="site_title">esehatena</h1>');
};

var addNaviBar = function() {
    $('#Main').append('<div class="navibar" id="nav"></div>')
    $('#nav').append('|<a id="nv_edit">編集</a>')
    $('#nav').append('|<a id="nv_top">トップ</a>')
    $('#nav').append('|<a id="nv_list">一覧</a>')
    $('#nav').append('|<a id="nv_home">ホーム</a>')
    $('#nav').append('|<a id="nv_new">新しい記事を作る</a>')
    $('#nav').append('|<a id="nv_close">△</a>|')

    $('#nv_top').click(function(){viewPage(0, 10);});
    $('#nv_list').click(viewEntryList);
    $('#nv_new').click(viewCreateForm);
    $('#nv_home').click(function(){viewEntry($('#screen'),'Home',$('#nv_edit'));});
    $('#nv_close').click(headerClose);
};

var headerClose = function() {
    $('#site_title').hide();
    $(this).unbind('click');
    $(this).bind('click', headerOpen);
    $(this).html('▽');
};
var headerOpen = function() {
    $('#site_title').show();
    $(this).unbind('click');
    $(this).bind('click', headerClose);
    $(this).html('△');
};

var addScreen = function() {
    $('#Main').append('<div id="screen"></div>')
};

var viewEntryList =function() {
    $.ajax({
        type:"get",
        url:"../api/v1/entries?fields=id,title,categories",
        contentType: 'application/json',
        dataType: "json",
        success: function(json_data) {
            $('#screen').html('<table id="entry_list"></table>');
            for (entry of json_data) {
                eid   = entry['entry']['id'];
                title = entry['entry']['title'];
                cat_str = entry['entry']['categories'].join(',');
                $('#entry_list').append(
                    '<tr><td class="elink">' + eid + '</td>' +
                    '<td><a>' + title + '</a>' +
                    '<div style="color:gray; font-size:0.8em">' + cat_str +
                    '</div></td></tr>');
            }                        
            $('.elink').click( function() {
                viewEntry($('#screen'), $(this).text(), $('#nv_edit'));
            });
        },
        error: function() {
            alert("Server Error. Pleasy try again later.");
        },
        complete: function() {
        }
    });
}; 

var viewEntry = function(jobj, entry_id, editobj) {
    $.ajax({
        type:"get",
        url:"../api/v1/entries/" + entry_id + '?fields=html',
        contentType: 'application/json',
        dataType: "json",
        success: function(json_data) {
            $(jobj).html(json_data['entry']['html']);
            if (editobj) {
                $(editobj).unbind('click');
                $(editobj).click( function() {viewEditForm(entry_id);} );
            }
        },
        error: function() {
            alert("Server Error. Pleasy try again later.");
        },
        complete: function() {
        }
    });
};

var viewPage = function(page, span) {
    $.ajax({
        type:"get",
        url:"../api/v1/entries?fields=id",
        contentType: 'application/json',
        dataType: "json",
        success: function(json_data) {
            $('#screen').html('');
            for (entry of json_data.slice(page*span, (page+1)*span)) {
                entry_id = entry['entry']['id'];
                div_id   = 'vw-' + entry_id;
                $('#screen').append('<div id="' + div_id +'"></div>')
                viewEntry($('#'+div_id), entry_id, null);
            }                        
        },
        error: function() {
            alert("Server Error. Pleasy try again later.");
        },
        complete: function() {
        }
    });
};

var viewEditForm = function(entry_id) {
    $('#screen').html('<h2 style="margin-top:0.8em;">「<span id="edit_title">' + entry_id + '</span>」の編集</h2>'
                      + '<div style="display:flex;">'
                      +   '<div style="padding:0.5em; width:50%">'
                      +       '<p style="font-size:0.8em;">editor</p>'
                      +       '<textarea id="source" style="width:100%;height:30em;"></textarea>'
                      +       '<div><input type="button" id="accept_btn" value="Accept" />&nbsp;<a id="cancel_btn">[(!)すべての編集内容を捨てて戻る]</a></div>'
                      +       '<p style="font-size:0.8em;">images</p>'
                      +       '<ul id="image_upload_pain"></ul>'
                      +   '</div>'
                      +   '<div style="padding:0.5em; width:50%">'
                      +       '<p style="font-size:0.8em;">preview</p>'
                      +       '<div id="preview_area" style="border:1px solid #666; background-color:#FFE;padding:0.5em;overflow:auto;height:30em;"></div>'
                      +   '</div>'
                      + '</div>')

    $('#cancel_btn').click(function(){viewEntry($('#screen'),entry_id,$('#nv_edit'));});
    $('#accept_btn').click(function(){ onAcceptEdit($(this), entry_id, $('#source'));});

    $.ajax({
        type:"get",
        url:"../api/v1/entries/"+entry_id+"?fields=title,html,source,images",
        contentType: 'application/json',
        dataType: "json",
        success: function(json_data) {
            $('#edit_title').html(json_data['entry']['title']);
            $('#source').val(json_data['entry']['source']);
            $('#preview_area').html(json_data['entry']['html']);
            for (img_name of json_data['entry']['images']) {
                $('#image_upload_pain').append('<li>' + img_name + '</li>');
            }
            
            $('#source').keyup( function(e){onPreview($(this), e,
                                                      entry_id,
                                                      $('#preview_area'),
                                                      $('#edit_title'));} );
        },
        error: function() {
            alert("Server Error. Pleasy try again later.");
        },
        complete: function() {
        }
    });
};

var viewCreateForm = function() {
    $('#screen').html('<h2 style="margin-top:0.8em;">「<span id="edit_title">新しいページ(仮)</span>」の編集</h2>'
                      + '<div style="display:flex;">'
                      +   '<div style="padding:0.5em; width:50%">'
                      +       '<p style="font-size:0.8em;">editor</p>'
                      +       '<textarea id="source" style="width:100%;height:30em;"></textarea>'
                      +       '<div><input type="button" id="accept_btn" value="Accept" /></div>'
                      +       '<p style="font-size:0.8em;">images</p>'
                      +       '<ul id="image_upload_pain"></ul>'
                      +   '</div>'
                      +   '<div style="padding:0.5em; width:50%">'
                      +       '<p style="font-size:0.8em;">preview</p>'
                      +       '<div id="preview_area" style="border:1px solid #666; background-color:#FFE;padding:0.5em;overflow:auto;height:30em;"></div>'
                      +   '</div>'
                      + '</div>')

    $('#accept_btn').click(function(){onAcceptCreate($(this), $('#source'));});
    $('#source').keyup( function(e){ onPreview($(this), e,
                                               '00000000-000000',
                                               $('#preview_area'),
                                               $('#edit_title') );} );
                                               
}


var onPreview = function(srcobj, e, entry_id, viewobj,titleobj) {
//    if ((e.keyCode != 13) && (e.keyCode != 8) && (e.keyCode != 46)) { return; } // cr, bs, del
    if (!$(srcobj).val()) {return;}

    var data = { id: entry_id,
                 source: $(srcobj).val() };
    $.ajax({
        type:"post",
        url:"../api/v1/preview",
        data:JSON.stringify(data),
        contentType: 'application/json',
        dataType: "json",
        success: function(json_data) {
            if (viewobj)  { $(viewobj).html(json_data['entry']['html']); }
            if (titleobj) { $(titleobj).html(json_data['entry']['title']); }
        },
        error: function() {
            alert("Server Error. Pleasy try again later.");
        },
        complete: function() {
        }
    });
};

var onAcceptEdit = function(btnobj, entry_id, srcobj) {
    var data = { entry: {id: entry_id,
                         source: $(srcobj).val()} };
    $(btnobj).attr("disabled", true);
    $.ajax({
        type:"put",
        url:"../api/v1/entries/" + entry_id + '?fields=html',
        data:JSON.stringify(data),
        contentType: 'application/json',
        dataType: "json",
        success: function(json_data) {
            $('#screen').html('<p>以下の内容で更新しました</p>'
                              + '<div id="update_view"></div>');
            $('#update_view').html(json_data['entry']['html']);
        },
        error: function() {
            alert("Server Error. Pleasy try again later.");
        },
        complete: function() {
            $(btnobj).attr("disabled", false);
        }
    });
};

var onAcceptCreate = function(btnobj, srcobj) {
    var data = { entry: {source: $(srcobj).val()} };
    $(btnobj).attr("disabled", true);
    $.ajax({
        type:"post",
        url:'../api/v1/entries?fields=html',
        data:JSON.stringify(data),
        contentType: 'application/json',
        dataType: "json",
        success: function(json_data) {
            $('#screen').html('<p>以下の内容で作成しました</p>'
                              + '<div id="update_view"></div>');
            $('#update_view').html(json_data['entry']['html']);
        },
        error: function() {
            alert("Server Error. Pleasy try again later.");
        },
        complete: function() {
            $(btnobj).attr("disabled", false);
        }
    });
};

var init = function() {
    addSiteHeader();
    addNaviBar();
    addScreen();
}

$(init)

