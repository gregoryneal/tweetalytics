$(document).ready(function () {
    google.charts.load('current', { 'packages': ['corechart', 'bar', 'calendar'] });
    $('#submit_username_button').removeClass('loading');

    var lock = false;
    $("#claws").submit(function (e) {
        e.preventDefault();
        //prevent people from spamming the button
        if (!lock) {
            lock = true;
            setTimeout(unlock, 1000);

            //set the loading gif to the little pacman one
            $('#submit_username_button').val('');
            $('#submit_username_button').addClass('loading');

            var idinput = $("#id-input").val();
            $("#id-input").removeClass('input-validation-error');

            $.ajax({
                type:   'POST',
                url:    '/stats', 
                data:   { "id-input": idinput }, //form data
                success: function (data) {
                    //console.log(typeof(data));
                    //console.log(data);
                    $('#submit_username_button').removeClass('loading');
                    $('#submit_username_button').val('»');

                    if (data.hasOwnProperty('result')) {
                        if (data.result == "FAIL") {
                            $("#id-input").addClass('input-validation-error');

                            if (data.message == 'request limit') {
                                $('#popupModal').modal({ backdrop: 'static' });
                            }
                        }
                    } else {
                        displayMetadata(data.metadata);
                        // Set a callback to run when the Google Visualization API is loaded.
                        google.charts.setOnLoadCallback(function () {
                            $('#user_data_container').removeAttr('hidden');
                            displayStats(data);
                        });
                    }
                },
                dataType:'json'}); //return data as a .json
        } else {
            //console.log("locked mother fucker, don't click this button again for 1 second");
        }
    });

    //release the button lock
    function unlock () {
        lock = false;
    }

    function displayMetadata(metadata) {
        $('#user-img').attr('src', metadata['profile_url']);
        $('#profile-banner').attr('src', metadata['profile_banner']);
        $('#screen-name-text').html('@'.concat(metadata['screen_name']));
        //$('#num-tweets').html(metadata['statuses_count']);
        $('#stat-caption').html('Data gathered from '.concat(metadata['statuses_count'], ' tweets.'));
    }

    function displayStats(data) {
        // stats is a javascript object converted from the JSON response
        //we gotta parse through all the data now to display it
        var stats = data.stats;
        var lowColor = '#ffffff';
        var highColor = '#'.concat(data.metadata.bg_color).toLowerCase();
        var chartColors = [highColor, lowColor];
        //console.log("color: ".concat(highColor));

        var wf = stats.word_frequency;
        var hf = stats.hashtag_frequency;
        var mf = stats.mentioned_user_frequency;
        var tt = stats.tweet_times;
        var st = stats.sentiment_timeline;

        //console.log("loaded stats");

        var stopwords = ['rt', 'amp', 'you', 'your', 'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'];
        //top 20 non stop words
        //stop iterating when it returns true
        var data = [['Word', 'Frequency']];

        for (var i = 0; i < wf.length; i++) {
            if (data.length >= 20) {
                break;
            }

            var word = wf[i][0];
            var numb = wf[i][1];

            var isStopWord = stopwords.indexOf(word.toLowerCase()) > -1;

            if (!isStopWord) {
                data.push([word, numb]);
            }
        }

        var wf_options = {
            chart: {
                title: 'word frequency'
            },
            colors: chartColors
        };

        var wfc = new google.charts.Bar($('#wf')[0]);
        wfc.draw(google.visualization.arrayToDataTable(data), google.charts.Bar.convertOptions(wf_options));

        //console.log("loaded word frequency");

//        data = [['hashtag', 'frequency']];
//        for (var i = 0; i < hf.length; i++) {
//            if (data.length >= 20) {
//                break;
//            }

//            var word = hf[i][0];
//            var numb = hf[i][1];

//            data.push([word, numb]);
//        }

//        var hf_options = {
//            chart: {
//                title: 'hashtag frequency'
//            },
//            colors: chartcolors
//        };

//        var hfc = new google.charts.bar($('#hf')[0]);
//        hfc.draw(google.visualization.arraytodatatable(data), google.charts.bar.convertoptions(hf_options));

//        //console.log("loaded hashtag frequency");

//        data = [['mentioned user', 'frequency']];
//        for (var i = 0; i < mf.length; i++) {
//            if (data.length >= 20) {
//                break;
//            }

//            var word = mf[i][0];
//            var numb = mf[i][1];

//            data.push([word, numb]);
//        }

//        var mf_options = {
//            chart: {
//                title: 'mentioned user frequency'
//            },
//            colors: chartcolors
//        };

//        var mfc = new google.charts.bar($('#mf')[0]);
//        mfc.draw(google.visualization.arraytodatatable(data), google.charts.bar.convertoptions(mf_options));

//        //console.log("loaded mentions frequency");

//        //create a day/hour heatmap to display average tweeting habits
//        var ydata = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
//        var xdata = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]; //hours in the day
//        var zdata = [];

//        for (var i = 0; i < ydata.length; i++) {
//            zdata.push(new array(xdata.length).fill(0));
//        }

//        for (var i = 0; i < tt.length; i++) {
//            //console.log(tt[i]);

//            var d = new date(date.parse(tt[i]));

//            var day = d.getday();
//            var hour = d.gethours();

//            //console.log(day);
//            //console.log(hour);

//            var z = zdata[day][hour];
//            //console.log(typeof (z));

//            zdata[day][hour] = z + 1;
//        }

//        var tt_trace = {
//            x: xdata,
//            y: ydata,
//            z: zdata,
//            type: 'heatmap',
//            name: 'tweetmap',
//            colorscale: [lowcolor, highcolor]
//        };

//        //plotly.newplot('hm', [tt_trace]);
//        //console.log("loaded tweetmap");

//        //create a calendar map to show tweets over time
//        var caltable = new google.visualization.datatable();
//        caltable.addcolumn('date', 'date');
//        caltable.addcolumn('number', 'num tweets');
//        cdata = [];

//        xdata = [];
//        pydata = [];
//        sydata = [];
//        nydata = [];
//        var d; //day
//        var s; //sentiment object
//        for (var i = 0; i < st.length; i++) { //looks like [ [date0, [pol0, sub0, n0]], [date1, [pol1, sub1, n1]], ... ]
//            d = st[i][0];
//            s = st[i][1];
//            var date = new date(date.parse(d));
//            //xdata.push(d);
//            //pydata.push(s[0]); //polarity first
//            //sydata.push(s[1]); //subjectivity second
//            //nydata.push(s[2]); //num tweets that day
//            cdata.push([date, s[2]]);
//        }

//        caltable.addrows(cdata);

//        var diff = new date(date.parse(st[st.length - 1][0])).getfullyear() - new date(date.parse(st[0][0])).getfullyear(); //number of years between first and last tweet on record
//        var calh = (diff + 1) * 175; //one year of charts is 175px tall i think
//        //console.log((diff+1).tostring().concat(' year charts: ').concat(calh.tostring()).concat(' px tall.'));

//        //create the tweeting timeline visualization
//        var calchart = new google.visualization.calendar($('#tt')[0]);
//        calopt = {
//            title: 'tweets over time',
//            height: calh
//        };
//        calchart.draw(caltable, calopt);
//        //console.log("loaded tweet timeline");
    }
}); 