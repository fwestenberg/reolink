<h1 class="code-line" data-line-start=0 data-line-end=1 ><a id="Reolink_Python_package_0"></a>Reolink Python package</h1>
<p class="has-line-data" data-line-start="2" data-line-end="3">This is a package implementing the Reolink IP camera API. Also it’s providing a way to subscribe to Reolink events, so real-time events can be received on a webhook.</p>
<h3 class="code-line" data-line-start=4 data-line-end=5 ><a id="Usage_4"></a>Usage</h3>
<pre><code class="has-line-data" data-line-start="7" data-line-end="39" class="language-python">api = camera_api.Api(<span class="hljs-string">'192.168.1.10'</span>, <span class="hljs-number">80</span>, <span class="hljs-string">'user'</span>, <span class="hljs-string">'mypassword'</span>)

<span class="hljs-comment"># get settings, like ports etc.:</span>
<span class="hljs-keyword">await</span> api.get_settings()

<span class="hljs-comment"># Store the subscribe port</span>
subscribe_port =  api.onvif_port

<span class="hljs-comment"># get the states:</span>
<span class="hljs-keyword">await</span> api.get_states()

<span class="hljs-comment"># print some state value:</span>
print(api.ir_state)

<span class="hljs-comment"># enable the infrared lights:</span>
<span class="hljs-keyword">await</span> api.set_ir_lights(<span class="hljs-keyword">True</span>)

<span class="hljs-comment"># logout</span>
<span class="hljs-keyword">await</span> api.logout()

<span class="hljs-comment"># Now subscribe to events, suppose our webhook url is http://192.168.1.11/webhook123</span>

sman = subscription_manager.Manager(<span class="hljs-string">'192.168.1.10'</span>, subscribePort, <span class="hljs-string">' user'</span>, <span class="hljs-string">'mypassword'</span>)
<span class="hljs-keyword">await</span> sman.subscribe(<span class="hljs-string">'http://192.168.1.11/webhook123'</span>)

<span class="hljs-comment"># After some minutes check the renew timer (keep the eventing alive):</span>
<span class="hljs-keyword">if</span> (sman.renewTimer &lt;= <span class="hljs-number">100</span>):
    <span class="hljs-keyword">await</span> sman.renew()

<span class="hljs-comment"># Unsubscribe</span>
<span class="hljs-keyword">await</span> sman.unsubscribe()
</code></pre>
