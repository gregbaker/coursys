function attendance_update() {
    fetch(refresh_url)
    .then(response => response.json())
    .then(data => {
        for ( const sid in data ) {
            htmx.swap(sid, data[sid], { swapStyle: 'outerHTML' });
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
function attendance_ready() {
    document.body.addEventListener("showSaved", function(e){
        const successNotification = window.createNotification({
            theme: 'success',
            showDuration: 5000
        })({ 
            message: e.detail.value
        });
    });

    setInterval(attendance_update, 6000);

    var table = $('#attendance').dataTable({
        "bPaginate": false,
        "bJQueryUI": true,
        "aaSorting": [[0, "asc"], [1, "asc"]],
	  });
}