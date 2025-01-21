var appState = {
    display: 'false'
};

$(window).on('load', function(){
    $.ajax({
        url: 'sendDisplay',
        success: function(response) {
            appState.display = response.display;
            console.log('display:', appState.display);
            updateFooVisibility();
        },
        error: function(xhr, status, error) {
            console.error('Error getting display state:', error);
            console.log('Status:', status);
            console.log('Response:', xhr.responseText);
        }
    });
});
$(window).on('load', function(){
    $.ajax({
        url: '/getFooState',
        method: 'GET',
        success: function(response) {
            if(response.fooHidden) {
                $("#foo").hide();
            }
        }
    });
});

function updateFooVisibility() {
    if (appState.display === 'true') {
        $("#foo").show();
    } else {
        $("#foo").hide();
    }
}

$(document).ready(function(){
    console.log(appState.display);
  
    $("#Cards").click(function() {
        $.ajax({
            url: $(this).data('url'),
            method: 'POST',
            success: function(response) {
                console.log('Cards added:', response.AddedCards);
            }
        });
    });

    $("#Restart").click(function() {
        appState.display = 'false';
        console.log('Display set to:', appState.display);
        updateFooVisibility();
        $.ajax({
            url: $(this).data('url'),
            method: 'POST',
            data: { display: appState.display },
            success: function(response) {
                console.log('gamestage:', response.gamestage);
            },
            error: function(xhr, status, error) {
                console.error('Error resetting game:', error);
                console.log('Status:', status);
                console.log('Response:', xhr.responseText);
            }
        });
    });
});

//perplexity convo https://www.perplexity.ai/search/var-display-false-window-on-lo-753qVXwaQQKg7V1u69fapg