from kivy.graphics import (RenderContext, Fbo, Color, ClearColor, ClearBuffers, Rectangle)
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock

header = '''
$HEADER$

uniform vec2 resolution;
uniform float time;
uniform vec2 mouse;

'''

shader_postprocessing = header + '''
uniform vec2 uvsize;
uniform vec2 uvpos;
void main(void)
{
    vec2 q = tex_coord0 * vec2(1, -1);
    vec2 uv = 0.5 + (q-0.5);//*(0.9);// + 0.1*sin(0.2*time));

    vec3 oricol = texture2D(texture0,vec2(q.x,1.0-q.y)).xyz;
    vec3 col;

    col.r = texture2D(texture0,vec2(uv.x+0.003,-uv.y)).x;
    col.g = texture2D(texture0,vec2(uv.x+0.000,-uv.y)).y;
    col.b = texture2D(texture0,vec2(uv.x-0.003,-uv.y)).z;

    col = clamp(col*0.5+0.5*col*col*1.2,0.0,1.0);
   
    col *= vec3(0.8,1.0,0.7);

    col *= 0.9+0.1*sin(10.0*time+uv.y*1000.0);

    col *= 0.97+0.03*sin(110.0*time);

    float comp = smoothstep( 0.2, 0.7, sin(time) );
    //col = mix( col, oricol, clamp(-2.0+2.0*q.x+3.0*comp,0.0,1.0) );

    gl_FragColor = vec4(col,1.0);
}
'''

class ShaderWidget(FloatLayout):

    # texture of the framebuffer
    texture = ObjectProperty(None)

    def __init__(self, **kwargs):
        # Instead of using canvas, we will use a RenderContext,
        # and change the default shader used.
        self.canvas = RenderContext(use_parent_projection=True,
                                    use_parent_modelview=True,
                                    use_parent_frag_modelview=True)

        self.canvas.shader.fs = shader_postprocessing

        with self.canvas:
            self.fbo = Fbo(size=self.size)
            self.fbo_color = Color(1, 1, 1, 1)
            self.fbo_rect = Rectangle()

        with self.fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()

        # call the constructor of parent
        # if they are any graphics object, they will be added on our new canvas
        super(ShaderWidget, self).__init__(**kwargs)

        # We'll update our glsl variables in a clock
        Clock.schedule_interval(self.update_glsl, 0)

    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = [float(v) for v in self.size]

    #
    # now, if we have new widget to add,
    # add their graphics canvas to our Framebuffer, not the usual canvas.
    #

    def add_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(ShaderWidget, self).add_widget(widget)
        self.canvas = c

    def remove_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(ShaderWidget, self).remove_widget(widget)
        self.canvas = c

    def on_size(self, instance, value):
        self.fbo.size = value
        self.texture = self.fbo.texture
        self.fbo_rect.size = value

    def on_pos(self, instance, value):
        self.fbo_rect.pos = value

    def on_texture(self, instance, value):
        self.fbo_rect.texture = value