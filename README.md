# What Is a Vector? — One Robot, Two Numbers, One Arrow

M3 topic: linear combinations in the plane. Predict a robot's final position by adding its displacements and scaling its commands. The robot's centre is its tracked position. The solid arrows show movements. Dashed guides measure components in fixed world axes.

## Personalize and rebuild on this Mac

The silent master is output/Vectors_Silent.mp4. Narration_Script.md has the full timed English take, and Storyboard.pdf has six illustrated scene entries.

~~~zsh
cd "/Users/jainilpatel/Desktop/M3Animation/M3_AnimationVideo_Vectors_StudentID"
nano project.json
~~~

Set STUDENT_NAME, STUDENT_ID and NARRATION_CREDIT. In nano save with Control-O, Return, Control-X. Use the preview to inspect three excerpts from the actual scene timeline.

~~~zsh
./produce.zsh preview
open "output/Vectors_MotionPreview.mp4"
./produce.zsh rebuild
open "output/Vectors_Silent.mp4"
~~~

Rebuild refreshes the master and the storyboard frames. To regenerate the PDF from the current master alone, use ./produce.zsh documents.

## Record and export

Play the master from 0:00 and read only the Speak column of the script. Follow the silent cues and leave the closing hold. In QuickTime Player use File → New Audio Recording, then save your take to recordings/. Voice Memos can also export an M4A.

~~~zsh
./produce.zsh voice "recordings/My Robot Vector Narration.m4a"
open "output/Vectors_Final.mp4"
~~~

Substitute your WAV, M4A or MP3 filename. The exporter measures the decoded recording and compares it with the five-minute picture before combining them. A mismatch over two seconds stops the export. Align the take to the timed script and retry. Smaller differences receive ending silence or a matching short credits hold. The original recording and complete speech are preserved. Before publishing the final file, the exporter checks 1080p/30 H.264, AAC stream duration, audio loudness, complete decoding and a runtime strictly below seven minutes. Listen for intelligibility and synchronization.

## Source and dependencies

Code/vectors.py contains the scene, robot chassis, geometry and timeline. The translated tip is always tail + displacement; the scalar slider and active tip share the same k. The robot and the leading end of its trail share a single position on each leg. The camera, origin and world scale are fixed. The three preview excerpts use the same drawing code as the master. Code/board.json supplies the storyboard text; Code/storyboard.py lays it out with master frames. Code/produce.py handles rendering, verification and audio export.

The launcher uses this project's .venv or its parent's compatible environment. This Apple Silicon build used Python 3.14.7, Manim Community 0.22.1, Cairo and TeX Live. The dependency lock is requirements.txt. On a fresh macOS checkout with Homebrew, run:

~~~zsh
brew install python@3.14 cairo pkg-config ffmpeg
"$(brew --prefix python@3.14)/bin/python3.14" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
~~~

Use a TeX Live installation with latex, standalone, preview and dvisvgm. The renderer also searches the project and parent portable .texlive trees. With BasicTeX, add /Library/TeX/texbin to PATH. Test the setup with ./produce.zsh preview.

## Credits and submission

Grant Sanderson's lesson informed the progression from three perspectives on vectors to coordinate columns, tip-to-tail addition and scaling. The project brief supplied the robot example. The graphics are native Manim geometry and the script was written for this film. [3Blue1Brown, Vectors, what even are they?](https://youtu.be/fNk_zzaMoSs) · [Official companion lesson](https://www.3blue1brown.com/lessons/vectors/)

OpenAI Codex wrote the narration and code, designed the visuals, rendered the movie and prepared the storyboard. Production used Python, NumPy, Manim Community/Cairo, LaTeX/dvisvgm, FFmpeg/ffprobe and ReportLab. The student supplies the final narration. The silent master contains no speech, effects or music.

Use this folder as the root of M3_AnimationVideo_Vectors_StudentID, replacing StudentID with your ID. Include the narrated MP4, source, configuration, script and storyboard in the public repository. Verify public access and submit the repository link to the instructor.
