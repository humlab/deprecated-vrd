#!/usr/bin/env ruby

gem 'tty-prompt'

require "logger"
require "tty-prompt"

filepath_raw_input= File.realpath(ARGV[0])
filename = File.basename(filepath_raw_input, File.extname(filepath_raw_input))

log_file = "video_attack_#{filename}.log"
$log = Logger.new("| tee -a #{log_file}") # note the pipe ( '|' )
$log.debug "Writing to \"#{log_file}\""
$log.info "Treating \"#{filepath_raw_input}\" as input"

# mirroring
def hflip input_file
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Flipping #{input_file} horizontally producing #{output_file}"

	`ffmpeg -i #{input_file} -vf hflip -c:a copy #{output_file}`
end

# mirroring
def vflip input_file
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Flipping #{input_file} vertically producing #{output_file}"

	`ffmpeg -i #{input_file} -vf vflip -c:a copy #{output_file}`
end

#def mashup input_file, output_file
#	$log.debug "Concatenating all files in #{input_file} producing #{output_file}"
#  `ffmpeg -f concat -safe 0 -i #{input_file} -c copy #{output_file}`
#end

# color overlay

# changes in contrast/brightness/gamma/luminance
# low contrast
# high contrast
# high brightness
# https://ffmpeg.org/ffmpeg-filters.html#eq
def eq(input_file, brightness=0, contrast=1, saturation=1, gamma=1)
  output_file = get_output_file_name(input_file, __method__, {'brightness' => brightness, 'contrast' => contrast, 'saturation' => saturation, 'gamma' => gamma})
  $log.debug "Re-encoding #{input_file} with brightness=#{brightness}, saturation=#{saturation}, gamma=#{gamma}, contrast=#{contrast} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf eq=brightness=#{brightness}:saturation=#{saturation}:gamma=#{gamma}:contrast=#{contrast} -c:a copy #{output_file}`
end

# time shift
def time_shift_speed_up_double input_file
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Re-encoding #{input_file} with double the playback speed (speed-up) producing #{output_file}"

  `ffmpeg -i #{input_file} -filter:v "setpts=0.5*PTS" -an #{output_file}`
end

def time_shift_speed_up_40x input_file
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Re-encoding #{input_file} with 40x the playback speed (speed up) producing #{output_file}"

  `ffmpeg -i #{input_file} -filter:v "setpts=PTS/40" -an #{output_file}`
end

def time_shift_slow_down_quarter input_file
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Re-encoding #{input_file} (assuming 30fps) with 1/4 the playback speed (slow down) producing #{output_file}"

  `ffmpeg -i #{input_file} -filter:v "minterpolate='mi_mode=mci:mc_mode=aobmc:vsbmc=1:fps=120',setpts=4*PTS" #{output_file}`
end

def get_output_file_name(input_file, attack, params={})
  extension = File.extname(input_file)
  filename = File.basename(input_file, extension)

  formatted_params = params.any? ? "_" + params.map { |k, v| "#{k}_#{v}" }.join("_") : ""

  "#{filename}_#{attack.to_s}#{formatted_params}#{extension}"
end

# frame loss

# frame addition

# zoom / crop
def zoom input_file
  output_file = get_output_file_name(input_file, __method__)

	$log.debug "Zooming in on #{input_file} producing #{output_file}"
  `ffmpeg -i #{input_file} -vf "scale=2*iw:-1, crop=iw/2:ih/2" -c:a copy #{output_file}`
end

# blur (gaussian, motion), https://medium.com/@allanlei/blur-out-videos-with-ffmpeg-92d3dc62d069
def blur(input_file, luma_radius=[2, 5, 10, 25, 50], chroma_radius=10, luma_power=1)
  luma_radius.each do |radius|
    params = {'luma_radius' => radius, 'chroma_radius' => chroma_radius, 'luma_power' => luma_power}

    output_file = get_output_file_name(input_file, __method__, params)
    $log.debug "Applying blur with params=#{params} on #{input_file} producing #{output_file}"
    
    `ffmpeg -i #{input_file} -filter_complex "[0:v]boxblur=luma_radius=#{radius}:chroma_radius=#{chroma_radius}:luma_power=#{luma_power}[blurred]" -map "[blurred]" #{output_file}`
  end
end

# add border, https://stackoverflow.com/a/56179969/5045375
def border input_file 
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding border to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -filter_complex "[0]pad=w=20+iw:h=20+ih:x=10:y=10:color=red" #{output_file}`
end

# noise addition (gaussian, white, random), https://stackoverflow.com/a/15795112/5045375
def noise input_file
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding noise to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -filter_complex "geq=random(1)*255:128:128;aevalsrc=-2+random(0)" #{output_file}`
end

# rotate

# Picture-in-picture

# Insert text

# Artifacts, https://stackoverflow.com/a/15795112/5045375
def artefact input_file
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding artifacts to #{input_file} producing #{output_file}"

	`ffmpeg -i #{input_file} -bsf:v noise -codec:a copy #{output_file}`
end

# https://yalantis.com/blog/experiments-with-ffmpeg-filters-and-frei0r-plugin-effects/
def sepia input_file
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding sepia tint to #{input_file} producing #{output_file}"
  
  `ffmpeg -i #{input_file} -filter_complex colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131 #{output_file}`
end

# https://yalantis.com/blog/experiments-with-ffmpeg-filters-and-frei0r-plugin-effects/
def vertigo input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding vertigo effect to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=vertigo:0.2 #{output_file}`
end

def vignette input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding vignette effect to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=vignette #{output_file}`
end

def sobel input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding sobel effect to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=sobel #{output_file}`
end

def invert_colors input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Inverting colors of #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=invert0r #{output_file}`
end

def rgb_noise input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding RGB noise to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=rgbnoise:0.2 #{output_file}`
end

def distorter input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding distortion to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=distort0r:0.05|0.0000001 #{output_file}`
end

def nervous input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Applying nervous effect to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=nervous #{output_file}`
end

def glow input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Applying glow effect to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=glow #{output_file}`
end

def baltan input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding baltan to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=baltan #{output_file}`
end

def cartoon input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding cartoon to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=cartoon #{output_file}`
end

def dither input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding dither to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=dither #{output_file}`
end

#def fish input_file
# Note: requires frei0r
#  output_file = get_output_file_name(input_file, __method__)
#  $log.debug "Adding fisheye effect to #{input_file} producing #{output_file}"
#
#  `ffmpeg -i #{input_file} -vf frei0r=defish0r:0.7:n:0.6:0 #{output_file}`
#end

def edgeglow input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding edgeglow effect to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=edgeglow #{output_file}`
end

def emboss input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding emboss to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=emboss #{output_file}`
end

def glitch input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding glitch to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=glitch0r #{output_file}`
end

def graffiti input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding graffiti to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=lightgraffiti #{output_file}`
end

def pixelizor input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding pixelation to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=pixeliz0r #{output_file}`
end

def posterize input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding posterization to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=posterize #{output_file}`
end

def primaries input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Reducing #{input_file} to primary colors producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=primaries #{output_file}`
end

def scanline input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding scanlines to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=scanline0r #{output_file}`
end

def softglow input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding softglow to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=softglow #{output_file}`
end

def iirblur input_file
  # Note: requires frei0r
  output_file = get_output_file_name(input_file, __method__)
  $log.debug "Adding iirblur to #{input_file} producing #{output_file}"

  `ffmpeg -i #{input_file} -vf frei0r=IIRblur #{output_file}`
end

prompt = TTY::Prompt.new

video_attacks = prompt.multi_select("Select video attacks") do |menu|
  menu.choice :primaries
  menu.choice :scanline
  menu.choice :softglow
  menu.choice :pixelizor
  menu.choice :posterize
  menu.choice :glitch
  menu.choice :graffiti
  menu.choice :edgeglow
  menu.choice :fish
  menu.choice :dither
  menu.choice :cartoon
  menu.choice :baltan
  menu.choice :hflip
  menu.choice :vflip
  menu.choice :zoom
  menu.choice :border
  menu.choice :blur
  menu.choice :eq
  menu.choice :time_shift_speed_up_double
  menu.choice :time_shift_speed_up_40x
  menu.choice :time_shift_slow_down_quarter
  menu.choice :slow_down
  menu.choice :artefact
  menu.choice :noise # Takes a long time to run!
  menu.choice :sepia
  menu.choice :vertigo 
  menu.choice :vignette
  menu.choice :sobel
  menu.choice :invert_colors
  menu.choice :rgb_noise
  menu.choice :distorter
  menu.choice :iirblur
  menu.choice :nervous
  menu.choice :glow
end

video_attacks.each { |video_attack| 
    $log.info "Applying \"#{video_attack}\" on \"#{filepath_raw_input}\""

    send(video_attack, filepath_raw_input)
}
