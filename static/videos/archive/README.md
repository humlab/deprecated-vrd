Contains a set of videos provided by Pelle Snickars that are in the common domain.

Files with a file-size larger than 100MB have been shortened in duration, by
removing video-material at the end of the video until their file-size was less
than that of 100MB. The reason for this is because Github places a strict
file-size limit of 100MB.

The original file-sizes and durations of the video-files before truncation
videos were (output was cleaned up from stderr-output, one thing that failed
was ffmpeg trying to determine the video duration of this file),

    function duration
        ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $argv
    end

    function pprint_info
        set -l filename $argv
        set -l runtime (duration $filename)
        set -l minutes (math $runtime / 60)m
        set -l seconds (math $runtime \% 60)s
        set -l size (du -hm $filename | awk '{print $1}')MB
        echo "$filename: $minutes$seconds ($size:$runtime)"
    end

    for f in (ls -S)
        pprint_info $f
    end
               
    ATW653(1944).mpg: 13m23.104000s (904MB:803.104000)
    ATW655(1944).mpg: 12m16.864000s (829MB:736.864000)
    ATW-550.mpg: 14m32.784000s (649MB:872.784000)
    ATW-644.mpg: 14m15.120000s (636MB:855.120000)
    ATW-645.mpg: 14m7.360000s (630MB:847.360000)
    ATW-652.mpg: 13m41.280000s (611MB:821.280000)
    ATW-651.mpg: 13m25.560000s (599MB:805.560000)
    ATW-649.mpg: 12m59.200000s (580MB:779.200000)
    ATW-650.mpg: 12m54.280000s (576MB:774.280000)
    SF2082.mp4: 12m56.280000s (549MB:776.280000)
    DW 580.mpg: 16m33.560000s (196MB:993.560000)
    DW 579.mpg: 15m47.616000s (186MB:947.616000)
    DW 577 (stum).mpg: 15m7.680000s (186MB:907.680000)
    ATW550(1942).mpg: 14m32.720000s (186MB:872.720000)
    DW 581.mpg: 15m9.440000s (179MB:909.440000)
    ATW547(1942).mpg: 13m39.000000s (175MB:819.000000)
    ATW625(1943).mpg: 12m59.520000s (166MB:779.520000)
    ATW650(1944).mpg: 12m57.080000s (166MB:777.080000)
    ATW654(1944).mpg: 12m50.240000s (164MB:770.240000)
    DW 578.mpg: 12m44.200000s (151MB:764.200000)
    SF2032.1.mov: 6m30.844078s (77MB:390.844078)
    panorama_augusti_1944.mp4: 16m2.240000s (73MB:962.240000)
    SF2059.mov: 0m45.295744s (33MB:45.295744)
    ATW700.mpg.asf: 10m23.987000s (19MB:623.987000)
    sf2001(1).mp4: 2m10.822622s (18MB:130.822622)
    sf2001.mp4: 2m10.822622s (18MB:130.822622)
    ATW701.mpg.asf: 8m18.671000s (15MB:498.671000)

To shorten video-files the following command was used

    ffmpeg -i {input_file} -to HH:MM:SS -c copy {output_file}

Looking at the list, we observe that seveal files are grouped
in the 800MB+, 600-700MB, 500-600MB, and 100-200MB range. 

Through trial-and-error, appropriate lengths were found. The
following was employed to guide the search, 

    function extension
        echo .(string split -m1 -r '.' "$argv")[2]
    end

    function shorten
        # input_file $argv[1], to $argv[2], output_file $argv[3]
        ffmpeg -i $argv[1] -to $argv[2] -c copy -y $argv[3] 2> /dev/null
        du -hm $argv[3]
    end

    function shorten_p # p for plural
        # argv[1] = filename, 
        set -l input $argv[1]
        set -l ext (extension $input)
        set -l name (basename $input $ext)

        shorten $input "00:01:00" (string join '_' $name '1')$ext
        shorten $input "00:01:30" (string join '_' $name '130')$ext
        shorten $input "00:02:00" (string join '_' $name '2')$ext
        shorten $input "00:02:30" (string join '_' $name '230')$ext
        shorten $input "00:03:00" (string join '_' $name '300')$ext
        shorten $input "00:03:30" (string join '_' $name '330')$ext
        shorten $input "00:04:00" (string join '_' $name '4')$ext
    end

and then baby-steps were taken until the file-size was as close 
to <100MB as possible. 

After running shorten_p it was possible to guess a suitable duration.
Once a line is printed exceeding 100MB Ctrl+C was pressed to avoid
creating additional videos.

To demonstrate the process, we have,

    ATW653(1944).mpg: 13m23.104000s (904MB:803.104000)
    
thus prompting

    shorten_p ATW653\(1944\).mpg 
    68      ATW653(1944)_1.mpg
    101     ATW653(1944)_130.mpg

ultimately resolving in

    function new
        # argv[2] = duration (HH:MM:SS)
        set -l input $argv[1]
        set -l ext (extension $input)
        set -l name (basename $input $ext)

        shorten $input $argv[2] (string join '_' $name 'new')$ext
    end

    static/videos> new ATW653\(1944\).mpg "00:01:28"
    99      ATW653(1944)_new.mpg

Eventually, a pattern emerged and `new` could essentially be invoked
directly without first consulting `shorten_p`.

Then clean things up,

    rm -f *_1.mpg # risk removing panorama_augusti_1944.mp4 if not explicit
    rm -f *_130.mpg 
    rm -f *_1.mp4
    rm -f *_130.mp4
    rm -f *_2*
    rm -f *_3*
    rm -f *_4*

And to compare,

    for f in (ls -hS)
        set -l ext (extension $f)
        set -l name (basename $f $ext)
        set -l new_one (string join '_' $name 'new')$ext

        if test -e $new_one
            pprint_info $f
            pprint_info $new_one
        end
    end

Yielding

    ATW653(1944).mpg: 13m23.104000s (904MB:803.104000)
    ATW653(1944)_new.mpg: 1m28.080000s (99MB:88.080000)
    ATW655(1944).mpg: 12m16.864000s (829MB:736.864000)
    ATW655(1944)_new.mpg: 1m28.080000s (99MB:88.080000)
    ATW-550.mpg: 14m32.784000s (649MB:872.784000)
    ATW-550_new.mpg: 2m14.080000s (99MB:134.080000)
    ATW-644.mpg: 14m15.120000s (636MB:855.120000)
    ATW-644_new.mpg: 2m14.080000s (99MB:134.080000)
    ATW-645.mpg: 14m7.360000s (630MB:847.360000)
    ATW-645_new.mpg: 2m14.080000s (99MB:134.080000)
    ATW-652.mpg: 13m41.280000s (611MB:821.280000)
    ATW-652_new.mpg: 2m14.080000s (99MB:134.080000)
    ATW-651.mpg: 13m25.560000s (599MB:805.560000)
    ATW-651_new.mpg: 2m14.080000s (99MB:134.080000)
    ATW-649.mpg: 12m59.200000s (580MB:779.200000)
    ATW-649_new.mpg: 2m14.080000s (99MB:134.080000)
    ATW-650.mpg: 12m54.280000s (576MB:774.280000)
    ATW-650_new.mpg: 2m14.080000s (99MB:134.080000)
    SF2082.mp4: 12m56.280000s (549MB:776.280000)
    SF2082_new.mp4: 2m17.120000s (99MB:137.120000)
    DW 580.mpg: 16m33.560000s (196MB:993.560000)
    DW 580_new.mpg: 8m25.080000s (99MB:505.080000)
    DW 579.mpg: 15m47.616000s (186MB:947.616000)
    DW 579_new.mpg: 8m25.120000s (99MB:505.120000)
    DW 577 (stum).mpg: 15m7.680000s (186MB:907.680000)
    DW 577 (stum)_new.mpg: 8m25.080000s (99MB:505.080000)
    ATW550(1942).mpg: 14m32.720000s (186MB:872.720000)
    ATW550(1942)_new.mpg: 8m5.040000s (99MB:485.040000)
    DW 581.mpg: 15m9.440000s (179MB:909.440000)
    DW 581_new.mpg: 8m25.120000s (99MB:505.120000)
    ATW547(1942).mpg: 13m39.000000s (175MB:819.000000)
    ATW547(1942)_new.mpg: 8m5.040000s (99MB:485.040000)
    ATW625(1943).mpg: 12m59.520000s (166MB:779.520000)
    ATW625(1943)_new.mpg: 8m5.040000s (99MB:485.040000)
    ATW650(1944).mpg: 12m57.080000s (166MB:777.080000)
    ATW650(1944)_new.mpg: 8m5.040000s (99MB:485.040000)
    DW 578.mpg: 12m44.200000s (151MB:764.200000)
    DW 578_new.mpg: 8m25.080000s (99MB:505.080000)

We adopt the newly created `_new` files by overwriting the previous ones through

    rename -f 's/_new//g' *

Thus leaving us with the final set of video files,

    for f in (ls -hS)
        pprint_info $f
    end

    ATW654(1944).mpg: 12m50.240000s (164MB:770.240000)
    ATW-652.mpg: 2m14.080000s (99MB:134.080000)
    ATW-649.mpg: 2m14.080000s (99MB:134.080000)
    ATW-644.mpg: 2m14.080000s (99MB:134.080000)
    ATW-645.mpg: 2m14.080000s (99MB:134.080000)
    ATW-550.mpg: 2m14.080000s (99MB:134.080000)
    ATW-651.mpg: 2m14.080000s (99MB:134.080000)
    ATW-650.mpg: 2m14.080000s (99MB:134.080000)
    SF2082.mp4: 2m17.120000s (99MB:137.120000)
    DW 577 (stum).mpg: 8m25.080000s (99MB:505.080000)
    DW 579.mpg: 8m25.120000s (99MB:505.120000)
    DW 581.mpg: 8m25.120000s (99MB:505.120000)
    DW 580.mpg: 8m25.080000s (99MB:505.080000)
    DW 578.mpg: 8m25.080000s (99MB:505.080000)
    ATW650(1944).mpg: 8m5.040000s (99MB:485.040000)
    ATW625(1943).mpg: 8m5.040000s (99MB:485.040000)
    ATW550(1942).mpg: 8m5.040000s (99MB:485.040000)
    ATW547(1942).mpg: 8m5.040000s (99MB:485.040000)
    ATW653(1944).mpg: 1m28.080000s (99MB:88.080000)
    ATW655(1944).mpg: 1m28.080000s (99MB:88.080000)
    SF2032.1.mov: 6m30.844078s (77MB:390.844078)
    panorama_augusti_1944.mp4: 16m2.240000s (73MB:962.240000)
    SF2059.mov: 0m45.295744s (33MB:45.295744)
    ATW700.mpg.asf: 10m23.987000s (19MB:623.987000)
    sf2001(1).mp4: 2m10.822622s (18MB:130.822622)
    sf2001.mp4: 2m10.822622s (18MB:130.822622)
    ATW701.mpg.asf: 8m18.671000s (15MB:498.671000)

Ultimately, Github rejected our push operation, and so <50MB was opted for instead
yielding,

    panorama_augusti_1944.mp4: 9m30.004000s (48MB:570.004000)
    DW_577_stum.mpg: 4m.120000s (47MB:240.120000)
    DW_581.mpg: 4m.040000s (47MB:240.040000)
    DW_578.mpg: 4m.120000s (47MB:240.120000)
    DW_579.mpg: 4m.040000s (47MB:240.040000)
    DW_580.mpg: 4m.040000s (47MB:240.040000)
    ATW5471942.mpg: 3m50.040000s (47MB:230.040000)
    ATW5501942.mpg: 3m50.040000s (47MB:230.040000)
    ATW6251943.mpg: 3m50.040000s (47MB:230.040000)
    ATW6501944.mpg: 3m50.040000s (47MB:230.040000)
    SF2082.mp4: 1m10.120000s (47MB:70.120000)
    ATW6541944.mpg: 3m45.120000s (46MB:225.120000)
    ATW6531944.mpg: 0m40.080000s (45MB:40.080000)
    ATW6551944.mpg: 0m40.080000s (45MB:40.080000)
    ATW-649.mpg: 1m.040000s (45MB:60.040000)
    ATW-644.mpg: 1m.040000s (45MB:60.040000)
    ATW-645.mpg: 1m.040000s (45MB:60.040000)
    ATW-652.mpg: 1m.040000s (45MB:60.040000)
    ATW-650.mpg: 1m.040000s (45MB:60.040000)
    ATW-550.mpg: 1m.040000s (45MB:60.040000)
    ATW-651.mpg: 1m.040000s (45MB:60.040000)
    SF2032.1.mov: 3m45.040000s (44MB:225.040000)
    SF2059.mov: 0m45.295744s (33MB:45.295744)
    ATW700.mpg.asf: 10m23.987000s (19MB:623.987000)
    sf20011.mp4: 2m10.822622s (18MB:130.822622)
    sf2001.mp4: 2m10.822622s (18MB:130.822622)
    ATW701.mpg.asf: 8m18.671000s (15MB:498.671000)
