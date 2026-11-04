#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 size;
    float extent;
    float radius;
    float power;
    float thickness;
    float angle;
    vec4 firstColor;
    vec4 lastColor;
};
layout(binding = 1) uniform sampler2D source;

// A rounded superellipse in logical pixels. Content remains unscaled.
float coverage(vec2 point, vec2 box, float r, float p) {
    vec2 q = abs(point - box * .5) - (box * .5 - r);
    float d = pow(pow(max(q.x, 0.), p) + pow(max(q.y, 0.), p), 1./p) - r;
    float aa = max(fwidth(d), .65);
    return 1. - smoothstep(-aa*.5, aa*.5, d);
}
vec3 toLab(vec3 c) {
    c = pow(max(c, vec3(0)), vec3(2.2));
    vec3 lms = mat3(.4122214708,.2119034982,.0883024619, .5363325363,.6806995451,.2817188376, .0514459929,.1073969566,.6299787005)*c;
    lms = pow(lms, vec3(1./3.));
    return mat3(.2104542553,1.9779984951,.0259040371, .7936177850,-2.4285922050,.7827717662, -.0040720468,.4505937099,-.8086757660)*lms;
}
vec3 fromLab(vec3 c) {
    vec3 lms = mat3(1,1,1, .3963377774,-.1055613458,-.0894841775, .2158037573,-.0638541728,-1.2914855480)*c;
    lms = lms*lms*lms;
    vec3 rgb = mat3(4.0767416621,-1.2684380046,-.0041960863, -3.3077115913,2.6097574011,-.7034186147, .2309699292,-.3413193965,1.7076147010)*lms;
    return pow(max(rgb,vec3(0)),vec3(1./2.2));
}
void main() {
    vec2 pos = qt_TexCoord0 * size;
    vec2 innerSize = size - vec2(2.*extent);
    vec2 uv = (pos - vec2(extent)) / innerSize;
    float outer = coverage(pos,size,radius+extent,power);
    float inside = coverage(pos-vec2(thickness), size-vec2(2.*thickness), max(0.,radius+extent-thickness),power);
    vec4 content = texture(source,clamp(uv,vec2(0),vec2(1)));
    float a = mod(angle,360.); vec2 g = qt_TexCoord0;
    if(a>270.) { g.y=1.-g.y; a=360.-a; }
    else if(a>180.) { g=1.-g; a-=180.; }
    else if(a>90.) { g.x=1.-g.x; a=180.-a; }
    float s=sin(radians(a));
    float t=clamp(g.y*s+g.x*(1.-s),0.,1.);
    vec4 edge=vec4(fromLab(mix(toLab(firstColor.rgb),toLab(lastColor.rgb),t)),mix(firstColor.a,lastColor.a,t));
    edge.rgb*=edge.a;
    fragColor = (content*inside + edge*(1.-inside))*outer*qt_Opacity;
}
