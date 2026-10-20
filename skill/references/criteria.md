# Every WCAG 2.1 A and AA criterion, and what the triage can say about it

Generated from `rules/wcag21.json` and `rules/coverage.json` by `tools/build_skill.py`. Do not edit by hand.

For each criterion and each format: **in part** means a check exists and a person judges the rest; **not checked** means it applies to every file and the tool does not look; **if present** means it applies only when the file has that kind of content. No criterion is ever reported as passed. *Who* names who can close the gap: the author, an expert, or a screen-reader task test (Route 3).

Criterion text is quoted from [WCAG 2.1](https://www.w3.org/TR/WCAG21/) (W3C Recommendation, 06 May 2025). Copyright © W3C® (MIT, ERCIM, Keio, Beihang). Criterion text quoted from the WCAG 2.1 Recommendation under the W3C Document License. [License](https://www.w3.org/copyright/document-license-2023/).

| Criterion | Level | Word | PowerPoint | PDF |
| :--- | :-: | :--- | :--- | :--- |
| 1.1.1 Non-text Content | A | in part | in part | in part |
| 1.2.1 Audio-only and Video-only (Prerecorded) | A | if present | if present | if present |
| 1.2.2 Captions (Prerecorded) | A | if present | if present | if present |
| 1.2.3 Audio Description or Media Alternative (Prerecorded) | A | if present | if present | if present |
| 1.2.4 Captions (Live) | AA | if present | if present | if present |
| 1.2.5 Audio Description (Prerecorded) | AA | if present | if present | if present |
| 1.3.1 Info and Relationships | A | in part | in part | in part |
| 1.3.2 Meaningful Sequence | A | not checked | not checked | not checked |
| 1.3.3 Sensory Characteristics | A | not checked | not checked | not checked |
| 1.3.4 Orientation | AA | if present | if present | if present |
| 1.3.5 Identify Input Purpose | AA | if present | if present | if present |
| 1.4.1 Use of Color | A | not checked | not checked | not checked |
| 1.4.2 Audio Control | A | if present | if present | if present |
| 1.4.3 Contrast (Minimum) | AA | not checked | not checked | not checked |
| 1.4.4 Resize Text | AA | not checked | not checked | not checked |
| 1.4.5 Images of Text | AA | not checked | not checked | not checked |
| 1.4.10 Reflow | AA | not checked | not checked | not checked |
| 1.4.11 Non-text Contrast | AA | not checked | not checked | not checked |
| 1.4.12 Text Spacing | AA | not checked | not checked | not checked |
| 1.4.13 Content on Hover or Focus | AA | if present | if present | if present |
| 2.1.1 Keyboard | A | if present | if present | if present |
| 2.1.2 No Keyboard Trap | A | if present | if present | if present |
| 2.1.4 Character Key Shortcuts | A | if present | if present | if present |
| 2.2.1 Timing Adjustable | A | if present | if present | if present |
| 2.2.2 Pause, Stop, Hide | A | if present | if present | if present |
| 2.3.1 Three Flashes or Below Threshold | A | if present | if present | if present |
| 2.4.1 Bypass Blocks | A | if present | if present | if present |
| 2.4.2 Page Titled | A | in part | in part | in part |
| 2.4.3 Focus Order | A | if present | if present | if present |
| 2.4.4 Link Purpose (In Context) | A | in part | not checked | not checked |
| 2.4.5 Multiple Ways | AA | if present | if present | if present |
| 2.4.6 Headings and Labels | AA | in part | not checked | not checked |
| 2.4.7 Focus Visible | AA | if present | if present | if present |
| 2.5.1 Pointer Gestures | A | if present | if present | if present |
| 2.5.2 Pointer Cancellation | A | if present | if present | if present |
| 2.5.3 Label in Name | A | if present | if present | if present |
| 2.5.4 Motion Actuation | A | if present | if present | if present |
| 3.1.1 Language of Page | A | in part | not checked | in part |
| 3.1.2 Language of Parts | AA | not checked | not checked | not checked |
| 3.2.1 On Focus | A | if present | if present | if present |
| 3.2.2 On Input | A | if present | if present | if present |
| 3.2.3 Consistent Navigation | AA | if present | if present | if present |
| 3.2.4 Consistent Identification | AA | if present | if present | if present |
| 3.3.1 Error Identification | A | if present | if present | if present |
| 3.3.2 Labels or Instructions | A | if present | if present | if present |
| 3.3.3 Error Suggestion | AA | if present | if present | if present |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA | if present | if present | if present |
| 4.1.1 Parsing | A | not checked | not checked | not checked |
| 4.1.2 Name, Role, Value | A | if present | if present | if present |
| 4.1.3 Status Messages | AA | if present | if present | if present |

## 1.1.1 Non-text Content (Level A)

> All non-text content that is presented to the user has a text alternative that serves the equivalent purpose, except for the situations listed below.
> - Controls, Input: If non-text content is a control or accepts user input, then it has a name that describes its purpose. (Refer to Success Criterion 4.1.2 for additional requirements for controls and content that accepts user input.)
> - Time-Based Media: If non-text content is time-based media, then text alternatives at least provide descriptive identification of the non-text content. (Refer to Guideline 1.2 for additional requirements for media.)
> - Test: If non-text content is a test or exercise that would be invalid if presented in text, then text alternatives at least provide descriptive identification of the non-text content.
> - Sensory: If non-text content is primarily intended to create a specific sensory experience, then text alternatives at least provide descriptive identification of the non-text content.
> - CAPTCHA: If the purpose of non-text content is to confirm that content is being accessed by a person rather than a computer, then text alternatives that identify and describe the purpose of the non-text content are provided, and alternative forms of CAPTCHA using output modes for different types of sensory perception are provided to accommodate different disabilities.
> - Decoration, Formatting, Invisible: If non-text content is pure decoration, is used only for visual formatting, or is not presented to users, then it is implemented in a way that it can be ignored by assistive technology.

[Understanding Non-text Content](https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html)

- **Word**: checked in part by `docx.image-missing-alt`; still to judge: whether alt text that exists says what the image conveys in this course. *Who:* the author.
- **PowerPoint**: checked in part by `pptx.image-missing-alt`; still to judge: whether alt text that exists says what the picture conveys; charts, SmartArt and grouped shapes are not checked. *Who:* the author.
- **PDF**: checked in part by `pdf.scanned-no-text`; still to judge: alt text on figures inside the tag tree is not read; only pages with no text at all are found. *Who:* an expert.

## 1.2.1 Audio-only and Video-only (Prerecorded) (Level A)

> For prerecorded audio-only and prerecorded video-only media, the following are true, except when the audio or video is a media alternative for text and is clearly labeled as such:
> - Prerecorded Audio-only: An alternative for time-based media is provided that presents equivalent information for prerecorded audio-only content.
> - Prerecorded Video-only: Either an alternative for time-based media or an audio track is provided that presents equivalent information for prerecorded video-only content.

[Understanding Audio-only and Video-only (Prerecorded)](https://www.w3.org/WAI/WCAG21/Understanding/audio-only-and-video-only-prerecorded.html)

- **Word**: if the file has embedded or linked audio or video; not checked: a transcript for audio-only, or a transcript or audio track for video-only. *Who:* the author.
- **PowerPoint**: if the file has embedded or linked audio or video; not checked: a transcript for audio-only, or a transcript or audio track for video-only. *Who:* the author.
- **PDF**: if the file has embedded or linked audio or video; not checked: a transcript for audio-only, or a transcript or audio track for video-only. *Who:* the author.

## 1.2.2 Captions (Prerecorded) (Level A)

> Captions are provided for all prerecorded audio content in synchronized media, except when the media is a media alternative for text and is clearly labeled as such.

[Understanding Captions (Prerecorded)](https://www.w3.org/WAI/WCAG21/Understanding/captions-prerecorded.html)

- **Word**: if the file has embedded or linked audio or video; not checked: captions on prerecorded video. *Who:* the author.
- **PowerPoint**: if the file has embedded or linked audio or video; not checked: captions on prerecorded video. *Who:* the author.
- **PDF**: if the file has embedded or linked audio or video; not checked: captions on prerecorded video. *Who:* the author.

## 1.2.3 Audio Description or Media Alternative (Prerecorded) (Level A)

> An alternative for time-based media or audio description of the prerecorded video content is provided for synchronized media, except when the media is a media alternative for text and is clearly labeled as such.

[Understanding Audio Description or Media Alternative (Prerecorded)](https://www.w3.org/WAI/WCAG21/Understanding/audio-description-or-media-alternative-prerecorded.html)

- **Word**: if the file has embedded or linked audio or video; not checked: audio description or a full text alternative for prerecorded video. *Who:* the author.
- **PowerPoint**: if the file has embedded or linked audio or video; not checked: audio description or a full text alternative for prerecorded video. *Who:* the author.
- **PDF**: if the file has embedded or linked audio or video; not checked: audio description or a full text alternative for prerecorded video. *Who:* the author.

## 1.2.4 Captions (Live) (Level AA)

> Captions are provided for all live audio content in synchronized media.

[Understanding Captions (Live)](https://www.w3.org/WAI/WCAG21/Understanding/captions-live.html)

- **Word**: if the file has live audio; not checked: captions on live audio; rare in a course file. *Who:* the author.
- **PowerPoint**: if the file has live audio; not checked: captions on live audio; rare in a course file. *Who:* the author.
- **PDF**: if the file has live audio; not checked: captions on live audio; rare in a course file. *Who:* the author.

## 1.2.5 Audio Description (Prerecorded) (Level AA)

> Audio description is provided for all prerecorded video content in synchronized media.

[Understanding Audio Description (Prerecorded)](https://www.w3.org/WAI/WCAG21/Understanding/audio-description-prerecorded.html)

- **Word**: if the file has embedded or linked audio or video; not checked: audio description for prerecorded video. *Who:* the author.
- **PowerPoint**: if the file has embedded or linked audio or video; not checked: audio description for prerecorded video. *Who:* the author.
- **PDF**: if the file has embedded or linked audio or video; not checked: audio description for prerecorded video. *Who:* the author.

## 1.3.1 Info and Relationships (Level A)

> Information, structure, and relationships conveyed through presentation can be programmatically determined or are available in text.

[Understanding Info and Relationships](https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html)

- **Word**: checked in part by `docx.fake-heading`, `docx.heading-skip`, `docx.table-no-header`; still to judge: lists typed by hand instead of list styles, merged table cells, text boxes, and whether the headings mark the real sections. *Who:* the author.
- **PowerPoint**: checked in part by `pptx.slide-no-title`, `pptx.table-no-header`; still to judge: lists, table structure beyond the header row, and grouped content. *Who:* the author.
- **PDF**: checked in part by `pdf.untagged`; still to judge: whether the tags that exist match the headings, lists and tables on the page. *Who:* an expert.

## 1.3.2 Meaningful Sequence (Level A)

> When the sequence in which content is presented affects its meaning, a correct reading sequence can be programmatically determined.

[Understanding Meaningful Sequence](https://www.w3.org/WAI/WCAG21/Understanding/meaningful-sequence.html)

- **Word**: not checked: reading order of text boxes and floating objects. *Who:* the author.
- **PowerPoint**: not checked: reading order: open the selection pane and read it from the bottom up. *Who:* the author.
- **PDF**: not checked: tag order against visual order; needs a screen reader. *Who:* an expert.

## 1.3.3 Sensory Characteristics (Level A)

> Instructions provided for understanding and operating content do not rely solely on sensory characteristics of components such as shape, color, size, visual location, orientation, or sound.

[Understanding Sensory Characteristics](https://www.w3.org/WAI/WCAG21/Understanding/sensory-characteristics.html)

- **Word**: not checked: instructions that rely on shape, colour, size or position, such as 'the box on the right'. *Who:* the author.
- **PowerPoint**: not checked: instructions that rely on shape, colour, size or position, such as 'the box on the right'. *Who:* the author.
- **PDF**: not checked: instructions that rely on shape, colour, size or position, such as 'the box on the right'. *Who:* the author.

## 1.3.4 Orientation (Level AA)

> Content does not restrict its view and operation to a single display orientation, such as portrait or landscape, unless a specific display orientation is essential.

[Understanding Orientation](https://www.w3.org/WAI/WCAG21/Understanding/orientation.html)

- **Word**: if the file has content locked to one orientation; not checked: content that locks the display to portrait or landscape; the files themselves rarely do. *Who:* an expert.
- **PowerPoint**: if the file has content locked to one orientation; not checked: content that locks the display to portrait or landscape; the files themselves rarely do. *Who:* an expert.
- **PDF**: if the file has content locked to one orientation; not checked: content that locks the display to portrait or landscape; the files themselves rarely do. *Who:* an expert.

## 1.3.5 Identify Input Purpose (Level AA)

> The purpose of each input field collecting information about the user can be programmatically determined when:
> - The input field serves a purpose identified in the Input Purposes for user interface components section; and
> - The content is implemented using technologies with support for identifying the expected meaning for form input data.

[Understanding Identify Input Purpose](https://www.w3.org/WAI/WCAG21/Understanding/identify-input-purpose.html)

- **Word**: if the file has form fields that ask about the user; not checked: form fields that collect information about the user identify their purpose. *Who:* an expert.
- **PowerPoint**: if the file has form fields that ask about the user; not checked: form fields that collect information about the user identify their purpose. *Who:* an expert.
- **PDF**: if the file has form fields that ask about the user; not checked: form fields that collect information about the user identify their purpose. *Who:* an expert.

## 1.4.1 Use of Color (Level A)

> Color is not used as the only visual means of conveying information, indicating an action, prompting a response, or distinguishing a visual element.

[Understanding Use of Color](https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html)

- **Word**: not checked: information carried by colour alone, such as red for due dates or colour-only chart series. *Who:* the author.
- **PowerPoint**: not checked: information carried by colour alone, such as red for due dates or colour-only chart series. *Who:* the author.
- **PDF**: not checked: information carried by colour alone, such as red for due dates or colour-only chart series. *Who:* the author.

## 1.4.2 Audio Control (Level A)

> If any audio on a web page plays automatically for more than 3 seconds, either a mechanism is available to pause or stop the audio, or a mechanism is available to control audio volume independently from the overall system volume level.

[Understanding Audio Control](https://www.w3.org/WAI/WCAG21/Understanding/audio-control.html)

- **Word**: if the file has audio that plays automatically; not checked: audio that plays on its own for more than three seconds can be paused or turned down. *Who:* the author.
- **PowerPoint**: if the file has audio that plays automatically; not checked: audio that plays on its own for more than three seconds can be paused or turned down. *Who:* the author.
- **PDF**: if the file has audio that plays automatically; not checked: audio that plays on its own for more than three seconds can be paused or turned down. *Who:* the author.

## 1.4.3 Contrast (Minimum) (Level AA)

> The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for the following:
> - Large Text: Large-scale text and images of large-scale text have a contrast ratio of at least 3:1;
> - Incidental: Text or images of text that are part of an inactive user interface component, that are pure decoration, that are not visible to anyone, or that are part of a picture that contains significant other visual content, have no contrast requirement.
> - Logotypes: Text that is part of a logo or brand name has no contrast requirement.

[Understanding Contrast (Minimum)](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)

- **Word**: not checked: text colour against its background; a contrast checker settles it. *Who:* the author.
- **PowerPoint**: not checked: text colour against its background; a contrast checker settles it. *Who:* the author.
- **PDF**: not checked: text colour against its background; a contrast checker settles it. *Who:* the author.

## 1.4.4 Resize Text (Level AA)

> Except for captions and images of text, text can be resized without assistive technology up to 200 percent without loss of content or functionality.

[Understanding Resize Text](https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html)

- **Word**: not checked: usually met by the reader's zoom; text inside images does not scale. *Who:* an expert.
- **PowerPoint**: not checked: usually met by the reader's zoom; text in fixed boxes can clip and text inside images does not scale. *Who:* an expert.
- **PDF**: not checked: usually met by the reader's zoom; text inside images does not scale. *Who:* an expert.

## 1.4.5 Images of Text (Level AA)

> If the technologies being used can achieve the visual presentation, text is used to convey information rather than images of text except for the following:
> - Customizable: The image of text can be visually customized to the user's requirements;
> - Essential: A particular presentation of text is essential to the information being conveyed.

[Understanding Images of Text](https://www.w3.org/WAI/WCAG21/Understanding/images-of-text.html)

- **Word**: not checked: text shown as a picture, such as a screenshot of a table or a pasted slide. *Who:* the author.
- **PowerPoint**: not checked: text shown as a picture, such as a screenshot of a table or a pasted slide. *Who:* the author.
- **PDF**: not checked: text shown as a picture, such as a screenshot of a table or a pasted slide. *Who:* the author.

## 1.4.10 Reflow (Level AA)

> Content can be presented without loss of information or functionality, and without requiring scrolling in two dimensions for:
> - Vertical scrolling content at a width equivalent to 320 CSS pixels;
> - Horizontal scrolling content at a height equivalent to 256 CSS pixels.
> Except for parts of the content which require two-dimensional layout for usage or meaning.

[Understanding Reflow](https://www.w3.org/WAI/WCAG21/Understanding/reflow.html)

- **Word**: not checked: depends on the reader's app; text boxes and wide tables resist reflow. *Who:* an expert.
- **PowerPoint**: not checked: slides are a fixed layout and do not reflow; the notes and outline view do. *Who:* an expert.
- **PDF**: not checked: reflow needs a tagged PDF; untagged files cannot reflow. *Who:* an expert.

## 1.4.11 Non-text Contrast (Level AA)

> The visual presentation of the following have a contrast ratio of at least 3:1 against adjacent color(s):
> - User Interface Components: Visual information required to identify user interface components and states, except for inactive components or where the appearance of the component is determined by the user agent and not modified by the author;
> - Graphical Objects: Parts of graphics required to understand the content, except when a particular presentation of graphics is essential to the information being conveyed.

[Understanding Non-text Contrast](https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html)

- **Word**: not checked: chart lines, icons and form-field borders against their background. *Who:* the author.
- **PowerPoint**: not checked: chart lines, icons and form-field borders against their background. *Who:* the author.
- **PDF**: not checked: chart lines, icons and form-field borders against their background. *Who:* the author.

## 1.4.12 Text Spacing (Level AA)

> In content implemented using markup languages that support the following text style properties, no loss of content or functionality occurs by setting all of the following and by changing no other style property:
> - Line height (line spacing) to at least 1.5 times the font size;
> - Spacing following paragraphs to at least 2 times the font size;
> - Letter spacing (tracking) to at least 0.12 times the font size;
> - Word spacing to at least 0.16 times the font size.
> Exception: Human languages and scripts that do not make use of one or more of these text style properties in written text can conform using only the properties that exist for that combination of language and script.

[Understanding Text Spacing](https://www.w3.org/WAI/WCAG21/Understanding/text-spacing.html)

- **Word**: not checked: depends on the reader's app; rarely something the file controls. *Who:* an expert.
- **PowerPoint**: not checked: depends on the reader's app; rarely something the file controls. *Who:* an expert.
- **PDF**: not checked: depends on the reader's app; rarely something the file controls. *Who:* an expert.

## 1.4.13 Content on Hover or Focus (Level AA)

> Where receiving and then removing pointer hover or keyboard focus triggers additional content to become visible and then hidden, the following are true:
> - Dismissible: A mechanism is available to dismiss the additional content without moving pointer hover or keyboard focus, unless the additional content communicates an input error or does not obscure or replace other content;
> - Hoverable: If pointer hover can trigger the additional content, then the pointer can be moved over the additional content without the additional content disappearing;
> - Persistent: The additional content remains visible until the hover or focus trigger is removed, the user dismisses it, or its information is no longer valid.
> Exception: The visual presentation of the additional content is controlled by the user agent and is not modified by the author.

[Understanding Content on Hover or Focus](https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html)

- **Word**: if the file has tooltips or pop-ups; not checked: tooltips or pop-ups that appear on hover or focus can be dismissed and stay put. *Who:* an expert.
- **PowerPoint**: if the file has tooltips or pop-ups; not checked: tooltips or pop-ups that appear on hover or focus can be dismissed and stay put. *Who:* an expert.
- **PDF**: if the file has tooltips or pop-ups; not checked: tooltips or pop-ups that appear on hover or focus can be dismissed and stay put. *Who:* an expert.

## 2.1.1 Keyboard (Level A)

> All functionality of the content is operable through a keyboard interface without requiring specific timings for individual keystrokes, except where the underlying function requires input that depends on the path of the user's movement and not just the endpoints.

[Understanding Keyboard](https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html)

- **Word**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: everything interactive works from the keyboard. *Who:* a screen-reader task test.
- **PowerPoint**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: everything interactive works from the keyboard. *Who:* a screen-reader task test.
- **PDF**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: everything interactive works from the keyboard. *Who:* a screen-reader task test.

## 2.1.2 No Keyboard Trap (Level A)

> If keyboard focus can be moved to a component of the page using a keyboard interface, then focus can be moved away from that component using only a keyboard interface, and, if it requires more than unmodified arrow or tab keys or other standard exit methods, the user is advised of the method for moving focus away.

[Understanding No Keyboard Trap](https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html)

- **Word**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: keyboard focus never gets stuck. *Who:* a screen-reader task test.
- **PowerPoint**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: keyboard focus never gets stuck. *Who:* a screen-reader task test.
- **PDF**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: keyboard focus never gets stuck. *Who:* a screen-reader task test.

## 2.1.4 Character Key Shortcuts (Level A)

> If a keyboard shortcut is implemented in content using only letter (including upper- and lower-case letters), punctuation, number, or symbol characters, then at least one of the following is true:
> - Turn off: A mechanism is available to turn the shortcut off;
> - Remap: A mechanism is available to remap the shortcut to include one or more non-printable keyboard keys (e.g., Ctrl, Alt);
> - Active only on focus: The keyboard shortcut for a user interface component is only active when that component has focus.

[Understanding Character Key Shortcuts](https://www.w3.org/WAI/WCAG21/Understanding/character-key-shortcuts.html)

- **Word**: if the file has macros or scripts; not checked: single-key shortcuts added by macros or scripts can be turned off or remapped. *Who:* an expert.
- **PowerPoint**: if the file has macros or scripts; not checked: single-key shortcuts added by macros or scripts can be turned off or remapped. *Who:* an expert.
- **PDF**: if the file has macros or scripts; not checked: single-key shortcuts added by macros or scripts can be turned off or remapped. *Who:* an expert.

## 2.2.1 Timing Adjustable (Level A)

> For each time limit that is set by the content, at least one of the following is true:
> - Turn off: The user is allowed to turn off the time limit before encountering it; or
> - Adjust: The user is allowed to adjust the time limit before encountering it over a wide range that is at least ten times the length of the default setting; or
> - Extend: The user is warned before time expires and given at least 20 seconds to extend the time limit with a simple action (for example, "press the space bar"), and the user is allowed to extend the time limit at least ten times; or
> - Real-time Exception: The time limit is a required part of a real-time event (for example, an auction), and no alternative to the time limit is possible; or
> - Essential Exception: The time limit is essential and extending it would invalidate the activity; or
> - 20 Hour Exception: The time limit is longer than 20 hours.

[Understanding Timing Adjustable](https://www.w3.org/WAI/WCAG21/Understanding/timing-adjustable.html)

- **Word**: if the file has a time limit; not checked: time limits can be turned off, adjusted or extended. *Who:* the author.
- **PowerPoint**: if the file has slide timings or a time limit; not checked: slides that advance on a timer can be slowed or stopped. *Who:* the author.
- **PDF**: if the file has a time limit; not checked: time limits can be turned off, adjusted or extended. *Who:* the author.

## 2.2.2 Pause, Stop, Hide (Level A)

> For moving, blinking, scrolling, or auto-updating information, all of the following are true:
> - Moving, blinking, scrolling: For any moving, blinking or scrolling information that (1) starts automatically, (2) lasts more than five seconds, and (3) is presented in parallel with other content, there is a mechanism for the user to pause, stop, or hide it unless the movement, blinking, or scrolling is part of an activity where it is essential; and
> - Auto-updating: For any auto-updating information that (1) starts automatically and (2) is presented in parallel with other content, there is a mechanism for the user to pause, stop, or hide it or to control the frequency of the update unless the auto-updating is part of an activity where it is essential.

[Understanding Pause, Stop, Hide](https://www.w3.org/WAI/WCAG21/Understanding/pause-stop-hide.html)

- **Word**: if the file has animation, animated images or auto-advancing content; not checked: moving, blinking or auto-updating content can be paused, stopped or hidden. *Who:* the author.
- **PowerPoint**: if the file has animation, animated images or auto-advancing content; not checked: moving, blinking or auto-updating content can be paused, stopped or hidden. *Who:* the author.
- **PDF**: if the file has animation, animated images or auto-advancing content; not checked: moving, blinking or auto-updating content can be paused, stopped or hidden. *Who:* the author.

## 2.3.1 Three Flashes or Below Threshold (Level A)

> Web pages do not contain anything that flashes more than three times in any one second period, or the flash is below the general flash and red flash thresholds.

[Understanding Three Flashes or Below Threshold](https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold.html)

- **Word**: if the file has flashing animation or video; not checked: nothing flashes more than three times a second. *Who:* the author.
- **PowerPoint**: if the file has flashing animation or video; not checked: nothing flashes more than three times a second. *Who:* the author.
- **PDF**: if the file has flashing animation or video; not checked: nothing flashes more than three times a second. *Who:* the author.

## 2.4.1 Bypass Blocks (Level A)

> A mechanism is available to bypass blocks of content that are repeated on multiple web pages.

[Understanding Bypass Blocks](https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html)

- **Word**: if the file has a set of related files rather than one file; not checked: a way to skip blocks of content that repeat across files. *Who:* the author.
- **PowerPoint**: if the file has a set of related files rather than one file; not checked: a way to skip blocks of content that repeat across files. *Who:* the author.
- **PDF**: if the file has a set of related files rather than one file; not checked: a way to skip blocks of content that repeat across files. *Who:* the author.

## 2.4.2 Page Titled (Level A)

> Web pages have titles that describe topic or purpose.

[Understanding Page Titled](https://www.w3.org/WAI/WCAG21/Understanding/page-titled.html)

- **Word**: checked in part by `docx.missing-title`; still to judge: whether the title describes the file. *Who:* the author.
- **PowerPoint**: checked in part by `pptx.missing-title`; still to judge: whether the title describes the deck. *Who:* the author.
- **PDF**: checked in part by `pdf.missing-title`; still to judge: whether the title describes the file; a title set from the file name needs a glance. *Who:* the author.

## 2.4.3 Focus Order (Level A)

> If a web page can be navigated sequentially and the navigation sequences affect meaning or operation, focusable components receive focus in an order that preserves meaning and operability.

[Understanding Focus Order](https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html)

- **Word**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: focus moves in an order that keeps the meaning. *Who:* a screen-reader task test.
- **PowerPoint**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: focus moves in an order that keeps the meaning. *Who:* a screen-reader task test.
- **PDF**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: focus moves in an order that keeps the meaning. *Who:* a screen-reader task test.

## 2.4.4 Link Purpose (In Context) (Level A)

> The purpose of each link can be determined from the link text alone or from the link text together with its programmatically determined link context, except where the purpose of the link would be ambiguous to users in general.

[Understanding Link Purpose (In Context)](https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html)

- **Word**: checked in part by `docx.link-text`; still to judge: whether link text that is not generic still names its destination; links in headers and footers are not read. *Who:* the author.
- **PowerPoint**: not checked: link text on slides. *Who:* the author.
- **PDF**: not checked: link text; fix it in the source and re-export. *Who:* the author.

## 2.4.5 Multiple Ways (Level AA)

> More than one way is available to locate a web page within a set of web pages except where the web page is the result of, or a step in, a process.

[Understanding Multiple Ways](https://www.w3.org/WAI/WCAG21/Understanding/multiple-ways.html)

- **Word**: if the file has a set of related files rather than one file; not checked: more than one way to find a file within the set. *Who:* the author.
- **PowerPoint**: if the file has a set of related files rather than one file; not checked: more than one way to find a file within the set. *Who:* the author.
- **PDF**: if the file has a set of related files rather than one file; not checked: more than one way to find a file within the set. *Who:* the author.

## 2.4.6 Headings and Labels (Level AA)

> Headings and labels describe topic or purpose.

[Understanding Headings and Labels](https://www.w3.org/WAI/WCAG21/Understanding/headings-and-labels.html)

- **Word**: checked in part by `docx.no-headings`, `docx.empty-heading`; still to judge: whether heading text describes its section. *Who:* the author.
- **PowerPoint**: not checked: whether slide titles and labels describe their content. *Who:* the author.
- **PDF**: not checked: whether headings and labels describe their content; fix them in the source. *Who:* the author.

## 2.4.7 Focus Visible (Level AA)

> Any keyboard operable user interface has a mode of operation where the keyboard focus indicator is visible.

[Understanding Focus Visible](https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html)

- **Word**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: keyboard focus is visible; mostly the reader's app. *Who:* a screen-reader task test.
- **PowerPoint**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: keyboard focus is visible; mostly the reader's app. *Who:* a screen-reader task test.
- **PDF**: if the file has links, form fields, buttons or other things a keyboard moves to; not checked: keyboard focus is visible; mostly the reader's app. *Who:* a screen-reader task test.

## 2.5.1 Pointer Gestures (Level A)

> All functionality that uses multipoint or path-based gestures for operation can be operated with a single pointer without a path-based gesture, unless a multipoint or path-based gesture is essential.

[Understanding Pointer Gestures](https://www.w3.org/WAI/WCAG21/Understanding/pointer-gestures.html)

- **Word**: if the file has content operated by gestures; not checked: anything operated by a path or multi-point gesture also works with a single pointer. *Who:* a screen-reader task test.
- **PowerPoint**: if the file has content operated by gestures; not checked: anything operated by a path or multi-point gesture also works with a single pointer. *Who:* a screen-reader task test.
- **PDF**: if the file has content operated by gestures; not checked: anything operated by a path or multi-point gesture also works with a single pointer. *Who:* a screen-reader task test.

## 2.5.2 Pointer Cancellation (Level A)

> For functionality that can be operated using a single pointer, at least one of the following is true:
> - No Down-Event: The down-event of the pointer is not used to execute any part of the function;
> - Abort or Undo: Completion of the function is on the up-event, and a mechanism is available to abort the function before completion or to undo the function after completion;
> - Up Reversal: The up-event reverses any outcome of the preceding down-event;
> - Essential: Completing the function on the down-event is essential.

[Understanding Pointer Cancellation](https://www.w3.org/WAI/WCAG21/Understanding/pointer-cancellation.html)

- **Word**: if the file has form fields or other controls; not checked: actions fire on release and can be cancelled. *Who:* a screen-reader task test.
- **PowerPoint**: if the file has form fields or other controls; not checked: actions fire on release and can be cancelled. *Who:* a screen-reader task test.
- **PDF**: if the file has form fields or other controls; not checked: actions fire on release and can be cancelled. *Who:* a screen-reader task test.

## 2.5.3 Label in Name (Level A)

> For user interface components with labels that include text or images of text, the name contains the text that is presented visually.

[Understanding Label in Name](https://www.w3.org/WAI/WCAG21/Understanding/label-in-name.html)

- **Word**: if the file has form fields or other controls; not checked: a control's accessible name contains its visible label. *Who:* an expert.
- **PowerPoint**: if the file has form fields or other controls; not checked: a control's accessible name contains its visible label. *Who:* an expert.
- **PDF**: if the file has form fields or other controls; not checked: a control's accessible name contains its visible label. *Who:* an expert.

## 2.5.4 Motion Actuation (Level A)

> Functionality that can be operated by device motion or user motion can also be operated by user interface components and responding to the motion can be disabled to prevent accidental actuation, except when:
> - Supported Interface: The motion is used to operate functionality through an accessibility supported interface;
> - Essential: The motion is essential for the function and doing so would invalidate the activity.

[Understanding Motion Actuation](https://www.w3.org/WAI/WCAG21/Understanding/motion-actuation.html)

- **Word**: if the file has content operated by device motion; not checked: anything operated by moving the device also works another way. *Who:* a screen-reader task test.
- **PowerPoint**: if the file has content operated by device motion; not checked: anything operated by moving the device also works another way. *Who:* a screen-reader task test.
- **PDF**: if the file has content operated by device motion; not checked: anything operated by moving the device also works another way. *Who:* a screen-reader task test.

## 3.1.1 Language of Page (Level A)

> The default human language of each web page can be programmatically determined.

[Understanding Language of Page](https://www.w3.org/WAI/WCAG21/Understanding/language-of-page.html)

- **Word**: checked in part by `docx.missing-language`; still to judge: whether the language set is the language of the text; the owner names it. *Who:* the author.
- **PowerPoint**: not checked: PowerPoint stores language on each run of text; check it under Review, Language. *Who:* the author.
- **PDF**: checked in part by `pdf.missing-language`; still to judge: whether the language set is the language of the text; the owner names it. *Who:* the author.

## 3.1.2 Language of Parts (Level AA)

> The human language of each passage or phrase in the content can be programmatically determined except for proper names, technical terms, words of indeterminate language, and words or phrases that have become part of the vernacular of the immediately surrounding text.

[Understanding Language of Parts](https://www.w3.org/WAI/WCAG21/Understanding/language-of-parts.html)

- **Word**: not checked: passages in another language are marked as that language. *Who:* the author.
- **PowerPoint**: not checked: passages in another language are marked as that language. *Who:* the author.
- **PDF**: not checked: passages in another language are marked as that language. *Who:* the author.

## 3.2.1 On Focus (Level A)

> When any user interface component receives focus, it does not initiate a change of context.

[Understanding On Focus](https://www.w3.org/WAI/WCAG21/Understanding/on-focus.html)

- **Word**: if the file has form fields or other controls; not checked: nothing changes context when an item receives focus. *Who:* an expert.
- **PowerPoint**: if the file has form fields or other controls; not checked: nothing changes context when an item receives focus. *Who:* an expert.
- **PDF**: if the file has form fields or other controls; not checked: nothing changes context when an item receives focus. *Who:* an expert.

## 3.2.2 On Input (Level A)

> Changing the setting of any user interface component does not automatically cause a change of context unless the user has been advised of the behavior before using the component.

[Understanding On Input](https://www.w3.org/WAI/WCAG21/Understanding/on-input.html)

- **Word**: if the file has form fields or other controls; not checked: changing a field's value does not change context without warning. *Who:* an expert.
- **PowerPoint**: if the file has form fields or other controls; not checked: changing a field's value does not change context without warning. *Who:* an expert.
- **PDF**: if the file has form fields or other controls; not checked: changing a field's value does not change context without warning. *Who:* an expert.

## 3.2.3 Consistent Navigation (Level AA)

> Navigational mechanisms that are repeated on multiple web pages within a set of web pages occur in the same relative order each time they are repeated, unless a change is initiated by the user.

[Understanding Consistent Navigation](https://www.w3.org/WAI/WCAG21/Understanding/consistent-navigation.html)

- **Word**: if the file has a set of related files rather than one file; not checked: repeated navigation appears in the same order across the set. *Who:* the author.
- **PowerPoint**: if the file has a set of related files rather than one file; not checked: repeated navigation appears in the same order across the set. *Who:* the author.
- **PDF**: if the file has a set of related files rather than one file; not checked: repeated navigation appears in the same order across the set. *Who:* the author.

## 3.2.4 Consistent Identification (Level AA)

> Components that have the same functionality within a set of web pages are identified consistently.

[Understanding Consistent Identification](https://www.w3.org/WAI/WCAG21/Understanding/consistent-identification.html)

- **Word**: if the file has a set of related files rather than one file; not checked: things that do the same job are labelled the same way across the set. *Who:* the author.
- **PowerPoint**: if the file has a set of related files rather than one file; not checked: things that do the same job are labelled the same way across the set. *Who:* the author.
- **PDF**: if the file has a set of related files rather than one file; not checked: things that do the same job are labelled the same way across the set. *Who:* the author.

## 3.3.1 Error Identification (Level A)

> If an input error is automatically detected, the item that is in error is identified and the error is described to the user in text.

[Understanding Error Identification](https://www.w3.org/WAI/WCAG21/Understanding/error-identification.html)

- **Word**: if the file has form fields; not checked: input errors are identified and described in text. *Who:* an expert.
- **PowerPoint**: if the file has form fields; not checked: input errors are identified and described in text. *Who:* an expert.
- **PDF**: if the file has form fields; not checked: input errors are identified and described in text. *Who:* an expert.

## 3.3.2 Labels or Instructions (Level A)

> Labels or instructions are provided when content requires user input.

[Understanding Labels or Instructions](https://www.w3.org/WAI/WCAG21/Understanding/labels-or-instructions.html)

- **Word**: if the file has form fields or fill-in blanks; not checked: fields and fill-in blanks have labels or instructions. *Who:* the author.
- **PowerPoint**: if the file has form fields or fill-in blanks; not checked: fields and fill-in blanks have labels or instructions. *Who:* the author.
- **PDF**: if the file has form fields or fill-in blanks; not checked: fields and fill-in blanks have labels or instructions. *Who:* the author.

## 3.3.3 Error Suggestion (Level AA)

> If an input error is automatically detected and suggestions for correction are known, then the suggestions are provided to the user, unless it would jeopardize the security or purpose of the content.

[Understanding Error Suggestion](https://www.w3.org/WAI/WCAG21/Understanding/error-suggestion.html)

- **Word**: if the file has form fields; not checked: known input errors come with a suggestion. *Who:* an expert.
- **PowerPoint**: if the file has form fields; not checked: known input errors come with a suggestion. *Who:* an expert.
- **PDF**: if the file has form fields; not checked: known input errors come with a suggestion. *Who:* an expert.

## 3.3.4 Error Prevention (Legal, Financial, Data) (Level AA)

> For web pages that cause legal commitments or financial transactions for the user to occur, that modify or delete user-controllable data in data storage systems, or that submit user test responses, at least one of the following is true:
> - Reversible: Submissions are reversible.
> - Checked: Data entered by the user is checked for input errors and the user is provided an opportunity to correct them.
> - Confirmed: A mechanism is available for reviewing, confirming, and correcting information before finalizing the submission.

[Understanding Error Prevention (Legal, Financial, Data)](https://www.w3.org/WAI/WCAG21/Understanding/error-prevention-legal-financial-data.html)

- **Word**: if the file has forms that submit legal, financial or test data; not checked: submissions with legal, financial or test consequences can be reversed, checked or confirmed. *Who:* an expert.
- **PowerPoint**: if the file has forms that submit legal, financial or test data; not checked: submissions with legal, financial or test consequences can be reversed, checked or confirmed. *Who:* an expert.
- **PDF**: if the file has forms that submit legal, financial or test data; not checked: submissions with legal, financial or test consequences can be reversed, checked or confirmed. *Who:* an expert.

## 4.1.1 Parsing (Level A)

> In content implemented using markup languages, elements have complete start and end tags, elements are nested according to their specifications, elements do not contain duplicate attributes, and any IDs are unique, except where the specifications allow these features.

[Understanding Parsing](https://www.w3.org/WAI/WCAG21/Understanding/parsing.html)

- **Word**: not checked: W3C's note on this criterion: always satisfied for any content using HTML or XML; Word files are XML packages. *Who:* an expert.
- **PowerPoint**: not checked: W3C's note on this criterion: always satisfied for any content using HTML or XML; PowerPoint files are XML packages. *Who:* an expert.
- **PDF**: not checked: a PDF is not markup in the HTML or XML sense; an expert checks the tag structure. *Who:* an expert.

## 4.1.2 Name, Role, Value (Level A)

> For all user interface components (including but not limited to: form elements, links and components generated by scripts), the name and role can be programmatically determined; states, properties, and values that can be set by the user can be programmatically set; and notification of changes to these items is available to user agents, including assistive technologies.

[Understanding Name, Role, Value](https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html)

- **Word**: if the file has form fields or other controls; not checked: controls expose a name, a role and their state to assistive technology. *Who:* an expert.
- **PowerPoint**: if the file has form fields or other controls; not checked: controls expose a name, a role and their state to assistive technology. *Who:* an expert.
- **PDF**: if the file has form fields or other controls; not checked: controls expose a name, a role and their state to assistive technology. *Who:* an expert.

## 4.1.3 Status Messages (Level AA)

> In content implemented using markup languages, status messages can be programmatically determined through role or properties such that they can be presented to the user by assistive technologies without receiving focus.

[Understanding Status Messages](https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html)

- **Word**: if the file has scripted status messages; not checked: status messages are announced without moving focus; rare in a file. *Who:* an expert.
- **PowerPoint**: if the file has scripted status messages; not checked: status messages are announced without moving focus; rare in a file. *Who:* an expert.
- **PDF**: if the file has scripted status messages; not checked: status messages are announced without moving focus; rare in a file. *Who:* an expert.
