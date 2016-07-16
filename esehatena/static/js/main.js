
var addSiteHeader = function() {
   $('#Main').append('<h1 class="site_title">esehatena</h1>');
};

var addNaviBar = function() {
    $('#Main').append('<div class="navibar" id="nav"></div>')
    $('#nav').append('|<a id="nv_edit">編集</a>')
    $('#nav').append('|<a id="nv_top">トップ</a>')
    $('#nav').append('|<a id="nv_list">一覧</a>')
    $('#nav').append('|<a id="nv_home">ホーム</a>')
    $('#nav').append('|<a id="nv_new">新しい記事を作る</a>')

    $('#nv_top').click(function(){viewPage(0, 10);});
    $('#nv_list').click(viewEntryList);
    $('#nv_new').click(addCreateForm);
    $('#nv_home').click(function(){viewEntry($('#screen'),'Home');});
};

var viewEntryList =function() {
    $.ajax({
        type:"get",
        url:"../api/v1/entries",
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
                viewEntry($('#screen'), $(this).text());
            });
        },
        error: function() {
            alert("Server Error. Pleasy try again later.");
        },
        complete: function() {
        }
    });
}; 

var viewEntry = function(jobj, entry_id) {
    $.ajax({
        type:"get",
        url:"../api/v1/entry/" + entry_id,
        contentType: 'application/json',
        dataType: "json",
        success: function(json_data) {
            $(jobj).html(
                json_data['entry']['html'])
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
        url:"../api/v1/entries",
        contentType: 'application/json',
        dataType: "json",
        success: function(json_data) {
            $('#screen').html('');
            for (entry of json_data.slice(page*span, (page+1)*span)) {
                entry_id = entry['entry']['id'];
                div_id   = 'vw-' + entry_id;
                $('#screen').append('<div id="' + div_id +'"></div>')
                viewEntry($('#'+div_id), entry_id);
            }                        
        },
        error: function() {
            alert("Server Error. Pleasy try again later.");
        },
        complete: function() {
        }
    });
};

var addCreateForm = function() {
    $('#screen').html('<form><div id="viewpanel"></div><div id="console"></div></form>')
    $('#viewpanel').append('<textarea name="source" id="src"/><div id="preview_area">')

    $('#src').keydown( function(e) {
        if (e.keyCode != 13) { return; }
        if (!$('#src').val()) {return;}

        var data = { id:'00000000_000000',
                     source: $('#src').val() };
        $.ajax({
            type:"post",
            url:"../api/v1/preview",
            data:JSON.stringify(data),
            contentType: 'application/json',
            dataType: "json",
            success: function(json_data) {
                $('#preview_area').html(
                    json_data['entry']['html']);
                $('#src').focus();
            },
            error: function() {
                alert("Server Error. Pleasy try again later.");
            },
            complete: function() {
            }
        });
    });
};

var init = function() {
    addSiteHeader();
    addNaviBar();
    $('#Main').append('<div id="screen"></div>')
}

$(init)

