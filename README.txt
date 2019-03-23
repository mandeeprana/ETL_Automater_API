
***********************************************************************************
** Chrome Install
***********************************************************************************
Add google repo.... JAY TO PROVIDE INSTRUCTIONS ...
yum install google-chrome-stable

***********************************************************************************
** Chrome Driver
***********************************************************************************
After installing Chrome download chromedriver to the /opt/google/chrome folder
and extract it.  Then make a symbolic link in the /usr/bin directory so it is
in the system path.

	wget https://chromedriver.storage.googleapis.com/2.42/chromedriver_linux64.zip

***********************************************************************************
** X Virtual Frame Buffer
***********************************************************************************
In order to run run chromedriver on a headless Linux server, one with no X11 server
the X virtual frame buffer will need to be installed that has the following 
dependencies.  

	[root@bucky opt]# yum deplist xorg-x11-server-Xvfb
	Loaded plugins: fastestmirror
	Repository google-chrome is listed more than once in the configuration
	Loading mirror speeds from cached hostfile
	 * base: centos.mirror.rafal.ca
	 * extras: centos.mirror.rafal.ca
	 * updates: centos.mirror.rafal.ca
	package: xorg-x11-server-Xvfb.x86_64 1.19.5-5.el7
	  dependency: /bin/sh
	   provider: bash.x86_64 4.2.46-30.el7
	  dependency: libGL.so.1()(64bit)
	   provider: mesa-libGL.x86_64 17.2.3-8.20171019.el7
	  dependency: libXau.so.6()(64bit)
	   provider: libXau.x86_64 1.0.8-2.1.el7
	  dependency: libXdmcp.so.6()(64bit)
	   provider: libXdmcp.x86_64 1.1.2-6.el7
	  dependency: libXfont2.so.2()(64bit)
	   provider: libXfont2.x86_64 2.0.1-2.el7
	  dependency: libaudit.so.1()(64bit)
	   provider: audit-libs.x86_64 2.8.1-3.el7_5.1
	  dependency: libc.so.6(GLIBC_2.17)(64bit)
	   provider: glibc.x86_64 2.17-222.el7
	  dependency: libcrypto.so.10()(64bit)
	   provider: openssl-libs.x86_64 1:1.0.2k-12.el7
	  dependency: libcrypto.so.10(libcrypto.so.10)(64bit)
	   provider: openssl-libs.x86_64 1:1.0.2k-12.el7
	  dependency: libdl.so.2()(64bit)
	   provider: glibc.x86_64 2.17-222.el7
	  dependency: libdl.so.2(GLIBC_2.2.5)(64bit)
	   provider: glibc.x86_64 2.17-222.el7
	  dependency: libgcc_s.so.1()(64bit)
	   provider: libgcc.x86_64 4.8.5-28.el7_5.1
	  dependency: libgcc_s.so.1(GCC_3.0)(64bit)
	   provider: libgcc.x86_64 4.8.5-28.el7_5.1
	  dependency: libgcc_s.so.1(GCC_3.3.1)(64bit)
	   provider: libgcc.x86_64 4.8.5-28.el7_5.1
	  dependency: libm.so.6()(64bit)
	   provider: glibc.x86_64 2.17-222.el7
	  dependency: libm.so.6(GLIBC_2.2.5)(64bit)
	   provider: glibc.x86_64 2.17-222.el7
	  dependency: libpam.so.0()(64bit)
	   provider: pam.x86_64 1.1.8-22.el7
	  dependency: libpam.so.0(LIBPAM_1.0)(64bit)
	   provider: pam.x86_64 1.1.8-22.el7
	  dependency: libpam_misc.so.0()(64bit)
	   provider: pam.x86_64 1.1.8-22.el7
	  dependency: libpam_misc.so.0(LIBPAM_MISC_1.0)(64bit)
	   provider: pam.x86_64 1.1.8-22.el7
	  dependency: libpixman-1.so.0()(64bit)
	   provider: pixman.x86_64 0.34.0-1.el7
	  dependency: libpthread.so.0()(64bit)
	   provider: glibc.x86_64 2.17-222.el7
	  dependency: libpthread.so.0(GLIBC_2.12)(64bit)
	   provider: glibc.x86_64 2.17-222.el7
	  dependency: libpthread.so.0(GLIBC_2.2.5)(64bit)
	   provider: glibc.x86_64 2.17-222.el7
	  dependency: libselinux.so.1()(64bit)
	   provider: libselinux.x86_64 2.5-12.el7
	  dependency: libsystemd.so.0()(64bit)
	   provider: systemd-libs.x86_64 219-57.el7_5.3
	  dependency: libsystemd.so.0(LIBSYSTEMD_209)(64bit)
	   provider: systemd-libs.x86_64 219-57.el7_5.3
	  dependency: libxshmfence.so.1()(64bit)
	   provider: libxshmfence.x86_64 1.2-1.el7
	  dependency: rtld(GNU_HASH)
	   provider: glibc.x86_64 2.17-222.el7
	   provider: glibc.i686 2.17-222.el7
	  dependency: xorg-x11-server-common >= 1.19.5-5.el7
	   provider: xorg-x11-server-common.x86_64 1.19.5-5.el7
	  dependency: xorg-x11-xauth
	   provider: xorg-x11-xauth.x86_64 1:1.0.9-1.el7

***********************************************************************************
** X Virtual Frame Buffer
***********************************************************************************
pip install pyvirtualdisplay

from pyvirtualdisplay import Display
from selenium import webdriver

# (800, 600)  (1024, 768)
display = Display(visible=0, size=(1024, 768))
display.start()

driver = webdriver.Chrome()
driver.get('https://automationpractice.com')
# save screenshot
driver.quit()
display.stop()
	
***********************************************************************************
** General Automation Test Sites
***********************************************************************************   
https://www.techbeamers.com/websites-to-practice-selenium-webdriver-online/