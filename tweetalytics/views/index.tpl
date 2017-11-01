% rebase('layout.tpl', title='Home Page')

<div class="jumbotron">
    <h1>tweetalytics</h1>
    <p class="lead">view analytics of your favorite tweeter, just enter their username or twitter id.</p>

	<form id="claws">
		<div class="input-group">
			<span class="input-group-addon" id="id-type">@</span>
			%if defined('invalid_id'):
				<input type="text" class="form-control input-validation-error" value="{{ invalid_id }}" id="id-input" name="id-input">
			%else:
				<input type="text" class="form-control" placeholder="BarackObama" id="id-input" name="id-input">
			%end
			<input type="submit" id="submit_username_button" class="btn btn-secondary loading" value="&raquo;" />
		</div>
	</form>
</div>

<div class="container-fluid" id="user_data_container" hidden>

	<div class="card-column">

		<div class="card mx-auto" id="meta-card">
			<img class="card-img-top" id="profile-banner" src="/static/images/default-banner.png">
			<div class="card-block">
				<img id="user-img" src="/static/images/default-profile.png">
				<h5 class="card-title" id="screen-name-text">@example</h5>
				<h6 class="card-subtitle text-muted" id="stat-caption"></h6>
			</div>
		</div>

		<div class="card mx-auto">
			<div class="card-header">
				Word Frequency
			</div>
			<div class="card-body" id="wf">						
			</div>
			<div class="card-footer text-muted">
				how often the person uses specific words
			</div>
		</div>

		<div class="card mx-auto">
			<div class="card-header">
				Hashtag Frequency
			</div>
			<div class="card-body" id="hf">						
			</div>
			<div class="card-footer text-muted">
				how often the person uses specific hashtags
			</div>
		</div>

		<div class="card mx-auto">
			<div class="card-header">
				User Mention Frequency
			</div>
			<div class="card-body" id="mf">						
			</div>
			<div class="card-footer text-muted">
				how often the person mentions specific users
			</div>
		</div>

		<div class="card mx-auto">
			<div class="card-header">
				Tweet Timeline
			</div>
			<div class="card-body" id="tt">						
			</div>
			<div class="card-footer text-muted">
				how often the person tweets over time
			</div>
		</div>

		<div class="card mx-auto">
			<div class="card-header">
				Tweetmap
			</div>
			<div class="card-body" id="hm">						
			</div>
			<div class="card-footer text-muted">
				a glimpse into the users tweeting habits by mapping the average times of day the user tweets
			</div>
		</div>

		<div class="card mx-auto">
			<div class="card-header">
				Semantic Timeline
			</div>
			<div class="card-body" id="st">						
			</div>
			<div class="card-footer text-muted">
				a plot of polarity: the positivity or negativity of the text, and subjectivity: a measure of the subjectiveness of the text
			</div>
		</div>

	</div>
</div>