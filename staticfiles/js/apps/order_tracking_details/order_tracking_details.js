const startPhaseIcons = ['Pickup Awaited', 'Pickup Scheduled', 'Picked Up', 'Booked', 'ReadyForReceive', 'PickupDone', 'ArrivedAtCarrierFacility', 'Softdata Upload'];
const deliveredPhaseIcons = ['Delivered'];

$(document).ready(function (){
    lastestCardStausIcon();
})

function lastestCardStausIcon(){
    for(let i = 0; i < STATUS_CARD_NUMBER ; i++){
        let card = $(`#statusCardIcon${i+1} .circle-frame`);
        let text = card.closest('.card').find('.statusCardText').text();
        if(text == 'Cancelled'){
            card.html('<i class="bi bi-x-octagon fs-1"></i>')
        }
        else if(text == 'Status will be available shortly.'){
            card.html('<i class="bi bi-question-octagon fs-1"></i>')
        }
        else if(startPhaseIcons.includes(text)){
            card.html('<i class="bi bi-file-earmark-text fs-1"></i>')
        }
        else if(deliveredPhaseIcons.includes(text)){
            card.html('<i class="bi bi-geo-alt fs-1"></i>')
        }
        else{
            card.html('<i class="bi bi-truck fs-1"></i>')
        }
    }
}

function gotoHome(){
    window.open('https://kyari.co/', '_blank');
}