This is the *first* editor.
------------------------------

Just plain **Markdown**, except that the input is sanitized:

Updates the authenticating user's current status, also known as tweeting. To upload an image to accompany the tweet, use POST statuses/update_with_media.

For each update attempt, the update text is compared with the authenticating user's recent tweets. Any attempt that would result in duplication will be blocked, resulting in a 403 error. Therefore, a user cannot submit the same status twice in a row.

While not rate limited by the API a user is limited in the number of tweets they can create at a time. If the number of updates posted by the user reaches the current allowed limit this method will return an HTTP 403 error.

# Parameters

:id:string:required:123

While not rate limited by the API a user is limited in the number of tweets they can create at a time. If the number of updates posted by the user reaches the current allowed limit this method will return an HTTP 403 error.

:trim_user:boolean:optional:true

Lorem ipsum dolor set amet

    {
        "name": "Tomas",
        "surname": "Hanacek",
    }

Note: This parameter will be ignored unless the author of the tweet this parameter references is mentioned within the status text. Therefore, you must include `@username`, where `username` is the author of the referenced tweet, within the update