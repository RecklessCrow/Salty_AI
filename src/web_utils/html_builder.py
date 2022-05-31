

def base_html_page(boxes, model_name, balance, current_match_info):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Title</title>
    
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.12.1.min.js"></script>
    
    <STYLE>
        
/* For Chrome or Safari */
progress {{
    -webkit-appearance: none;
    appearance: none;
}}
#redbar::-webkit-progress-value {{
    background: red;
}}
#redbar::-moz-progress-bar {{
    background: red;
}}
#bluebar::-webkit-progress-value {{
    background: blue;
}}
#bluebar::-moz-progress-bar {{
    background: blue;
}}

h1, h2, h3, h4, h5, h6, h7
{{
font-weight: normal;
}}

.sidenav {{
  height: 100%;
  width: 240px;
  position: fixed;
  z-index: 1;
  top: 0;
  left: 0;
  background-color: #181818;
  overflow-x: hidden;
  padding-top: 20px;
}}

body {{
  font-family: Helvetica;
}}

.sidenav a {{
  padding: 6px 8px 6px 16px;
  text-decoration: none;
  font-size: 16px;
  color: #B3B3B3;
  display: block;
}}


.sidenav a:hover {{
  color: #f1f1f1;
}}

/* Style page content */
.main {{
  margin-left: 220px;
  padding: 0px 10px;
}}
    </STYLE>
</head>
<body style="background-color: #121212">

<div class="sidenav">
    <h2 class=display-4 style="color: #B3B3B3;margin-left: 15px;">Menu</h2>
  <a href="#">Home</a>
  <a href="#">Model1</a>
  <a href="#">Model2</a>
</div>

<Div class="main" style="background-color: #121212">
    <h2 style="font-size: 4rem; color: #FFFFFF; margin-left: 15px;padding-top: 30px;">{model_name}</h2>
    <Div id="balance">
    <h3 style="font-size: 2rem; color: #FFFFFF; margin-left: 30px;margin-top: -40px;">Balance: ${balance:<9,}</h3>
    </Div>
    
    <Div style="width: 1560px; height: 500px;">
        <Div id="plot1" style="width: 960px; height: 500px;display:inline-block;"></Div>
        <Div id="plot2" style="width: 500px; height: 500px;display:inline-block;"></Div>
    </Div>


    <Div style="
        width: 100%;
        height: 100%;
        background-color: #404040">

        <Div style="
            width: 1100px;
            height: 700px;
            margin-left: 40px;
            padding-top: 20px;">

            <Div style="width: 400px;
                height: 600px;
                border-style: solid;
                display: inline-block;
                background-color: lightgrey;
                vertical-align: top">

                <Div style="font-size: 2rem;text-align: center;padding: 10px 0px 0px 0px;"> Feed History </Div>
                <Div id="boxes"> {boxes} </Div>

            </Div>

            <Div id="current_match_info" style="display: inline-block">{current_match_info}</Div>

        </Div>
    </div>
</div>

<script> 
$(document).ready(function(){{
setInterval(function(){{
      $("#current_match_info").load(" #current_match_info > *");
      $("#boxes").load(" #boxes > *");
      $("#balance").load(" #balance > *");
      
}}, 3000);
}});
</script>

<script> 
$(document).ready(function(){{
    $("#plot1").load("plot1.html");
    $("#plot2").load("plot2.html");
    setInterval(function(){{
          $("#plot1").load("plot1.html");
          $("#plot2").load("plot2.html");
    }}, 30000);
}});
</script>


</body>
</html>
    """


def create_feed_box(team_prediction, predicted_correct, confidence_level, balance_diff, odds, red_name, blue_name):
    return f"""<DIV style="
           backgroundColor: lightgrey;
           border-style: solid;
           width: 90%;
           margin-top: 10px;
           margin-left: 5%;
           height: 60px;
           text-align: center;">
        <DIV style="text-align: center">
    
            <DIV style="
            display:inline-block;
            width: 100px;
            font-size: 0.7rem;
            text-align: right;
            text-decoration: {'underline' if team_prediction == 'red' else 'none'};
            color: red;">
                {red_name}
            </DIV>
    
            <DIV style="
            display:inline-block;
            width: 40px;
            font-size: 0.7rem;
            text-align: Center;
            color: #181818">
                VS
            </DIV>
    
            <DIV style="
            display:inline-block;
            width: 100px;
            font-size: 0.7rem;
            text-align: left;
            text-decoration: {'underline' if team_prediction == 'blue' else 'none'};
            color: blue;">
                {blue_name}
            </DIV>
    
        </DIV>
    
        <DIV>
            Predicted {"Correctly" if predicted_correct else "Incorrectly"}! ({confidence_level:>6.2%} Confidence)
        </DIV>
    
        <DIV>
    
            <DIV style="color: {'green' if balance_diff > 0 else 'red'}; display: inline-block;width: 100px;align-text: right">
                {"+" if balance_diff > 0 else "-"}${abs(int(balance_diff)):,}
            </DIV>
    
                <DIV style="
                        display:inline-block;
                        width: 100px;
                        font-size: 0.7rem;
                        padding-left: 0.5rem">
                    popular odds:
                </DIV>
    
                <progress id="redbar" value="{100 / odds[1]}" max="100" style="height: 5px; width: 50px;transform: rotate(180deg);display: inline-block; margin-right: -5px;margin-top -5px;"></progress>
                <progress id="bluebar" value="{100 / odds[0]}" max="100" style="height: 5px; width: 50px;display: inline-block;margin-top -5px;"></progress>
    
        </DIV>
    </DIV>
    """


def create_current_match(match_confidence, team_prediction, red_name, blue_name, bet_amount):
    return f"""
        <Div style="
            width: 500px;
            height: 200px;
            border-style: solid;
            display: inline-block;
            vertical-align: top;
            text-align: center;
            background-color: lightgrey;">
        <Div style="
                width: 500px;
                padding: 10px 0px 10px 0px;
                font-size: 2rem;
                text-align: center;
                color: #181818;">
            Current Matchup
        </Div>
    
        <Div style="
                width: 500px;
                font-size: 1.0rem;
                text-align: center;
                color: #181818;">
            Confidence: {match_confidence:>6.2%}
        </Div>
    
    
    
        <Div style="width: 500px; text-align: center;">
             <Div>
                 <progress id="redbar" value="{match_confidence * 100 if team_prediction == 'red' else 0}" max="100" style="height: 30px; width: 200px;transform: rotate(180deg);display: inline-block; margin-right: -5px;"></progress>
                 <progress id="bluebar" value="{match_confidence * 100 if team_prediction == 'blue' else 0}" max="100" style="height: 30px; width: 200px;display: inline-block;"></progress>
             </Div>
        </Div>
    
    
        <DIV style="text-align: center; width: 500px;padding: 10px 0px;">
    
            <DIV style="
            display:inline-block;
            width: 200px;
            font-size: 0.8rem;
            text-align: right;
            color: red;">
                    {red_name}
            </DIV>
    
            <DIV style="
            display:inline-block;
            width: 80px;
            font-size: 1.2rem;
            text-align: Center;
            color: #181818">
                VS
            </DIV>
    
            <DIV style="
            display:inline-block;
            width: 200px;
            font-size: 0.8rem;
            text-align: left;
            color: blue;">
                {blue_name}
            </DIV>
    
        </DIV>
        
        <DIV style="
            width: 500px;
            font-size: 1.2rem;
            text-align: center;
            color: {'blue' if team_prediction == 'blue' else 'red'};">
                Betting ${bet_amount:,} on {blue_name if team_prediction == 'blue' else red_name}!
        </DIV>
        
        </DIV>
    </Div>
    """


def update_current_match(match_confidence, team_prediction, red_name, blue_name, odds, award_amount, bet_amount):
    return f"""
            <Div style="
                width: 500px;
                height: 200px;
                border-style: solid;
                display: inline-block;
                vertical-align: top;
                text-align: center;
                background-color: lightgrey;">
            <Div style="
                    width: 500px;
                    padding: 10px 0px 10px 0px;
                    font-size: 2rem;
                    text-align: center;
                    color: #181818;">
                Current Matchup
            </Div>

            <Div style="
                    width: 500px;
                    font-size: 1.0rem;
                    text-align: center;
                    color: #181818;">
                Confidence: {match_confidence:>6.2%}
            </Div>



            <Div style="width: 500px; text-align: center;">
                 <Div>
                     <progress id="redbar" value="{match_confidence * 100 if team_prediction == 'red' else 0}" max="100" style="height: 30px; width: 200px;transform: rotate(180deg);display: inline-block; margin-right: -5px;"></progress>
                     <progress id="bluebar" value="{match_confidence * 100 if team_prediction == 'blue' else 0}" max="100" style="height: 30px; width: 200px;display: inline-block;"></progress>
                 </Div>
            </Div>


            <DIV style="text-align: center; width: 500px;padding: 10px 0px;">

                <DIV style="
                display:inline-block;
                width: 200px;
                font-size: 0.8rem;
                text-align: right;
                color: red;">
                    {red_name}
                </DIV>

                <DIV style="
                display:inline-block;
                width: 80px;
                font-size: 1.2rem;
                text-align: Center;
                color: #181818">
                    VS
                </DIV>

                <DIV style="
                display:inline-block;
                width: 200px;
                font-size: 0.8rem;
                text-align: left;
                color: blue;">
                    {blue_name}
                </DIV>

            </DIV>
            
            <DIV>
    <DIV style="text-align: center; width: 500px">

        <DIV style="
        display:inline-block;
        width: 200px;
        font-size: 0.8rem;
        text-align: right;
        color: red;">
            {"+" if team_prediction == "red" else "-"} ${int(award_amount) if team_prediction == "red" else int(bet_amount):,}     ({odds[0]})
        </DIV>

        <DIV style="
        display:inline-block;
        width: 60px;
        font-size: 0.9rem;
        text-align: Center;
        color: #181818">
            ODDS
        </DIV>

        <DIV style="
        display:inline-block;
        width: 200px;
        font-size: 0.8rem;
        text-align: left;
        color: blue;">
            ({odds[1]})     {"+" if team_prediction == "blue" else "-"} ${int(award_amount) if team_prediction == "blue" else int(bet_amount):,}
        </DIV>

    </DIV>

    <DIV style="text-align: center; width: 500px;margin-top: -10px">
        <progress id="redbar" value="{100 / odds[1]}" max="100" style="height: 5px; width: 100px;transform: rotate(180deg);display: inline-block; margin-right: -5px;"></progress>
        <progress id="bluebar" value="{100 / odds[0]}" max="100" style="height: 5px; width: 100px;display: inline-block;"></progress>
    </DIV>

</DIV>       
</Div>
"""

