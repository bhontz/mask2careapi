## Mask2Care Project

Team Mask2Care's 2021 Technovation Challenge Thunkable app extension.

Endpoints:

#### orderoptions?items=<URL of jpg containing a face>

This endpoint returns a json structure with two keys error and items.  Error has a value of "ok" when all is well, otherwise, error's value represents an error message.  Errors can occur if a face isn't found within the image or facial landmarks can't be derived from the image.

The items key contains a list of six different jpg images, each containing the face jpg provided as input with a mask filter placed on top.