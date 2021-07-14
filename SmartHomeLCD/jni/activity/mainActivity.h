/***********************************************
/gen auto by zuitools
***********************************************/
#ifndef __MAINACTIVITY_H__
#define __MAINACTIVITY_H__


#include "app/Activity.h"
#include "entry/EasyUIContext.h"

#include "uart/ProtocolData.h"
#include "uart/ProtocolParser.h"

#include "utils/Log.h"
#include "control/ZKDigitalClock.h"
#include "control/ZKButton.h"
#include "control/ZKCircleBar.h"
#include "control/ZKDiagram.h"
#include "control/ZKListView.h"
#include "control/ZKPointer.h"
#include "control/ZKQRCode.h"
#include "control/ZKTextView.h"
#include "control/ZKSeekBar.h"
#include "control/ZKEditText.h"
#include "control/ZKVideoView.h"
#include "window/ZKSlideWindow.h"

/*TAG:Macro宏ID*/
#define ID_MAIN_Textview6    50006
#define ID_MAIN_Textview12    50012
#define ID_MAIN_ButtonSave    20015
#define ID_MAIN_ListviewMin    80006
#define ID_MAIN_ListviewHour    80007
#define ID_MAIN_ListviewDay    80005
#define ID_MAIN_Listviewmonth    80008
#define ID_MAIN_ListviewYear    80010
#define ID_MAIN_Window7    110011
#define ID_MAIN_Textview18    50019
#define ID_MAIN_Textview17    50018
#define ID_MAIN_Button10    20014
#define ID_MAIN_Button1    20013
#define ID_MAIN_Textview11    50011
#define ID_MAIN_Textview3    50003
#define ID_MAIN_Window4    110006
#define ID_MAIN_SubItem2    20005
#define ID_MAIN_Listview2    80002
#define ID_MAIN_Textview10    50010
#define ID_MAIN_Textview1    50001
#define ID_MAIN_Window3    110005
#define ID_MAIN_Textview16    50016
#define ID_MAIN_Textview15    50015
#define ID_MAIN_Textview14    50014
#define ID_MAIN_Button9    20011
#define ID_MAIN_Button8    20010
#define ID_MAIN_Button7    20009
#define ID_MAIN_Button6    20008
#define ID_MAIN_Button5    20007
#define ID_MAIN_Button4    20006
#define ID_MAIN_Textview13    50013
#define ID_MAIN_ListviewTempture    80003
#define ID_MAIN_Textview9    50009
#define ID_MAIN_Textview2    50002
#define ID_MAIN_Window2    110004
#define ID_MAIN_TextviewMode    50017
#define ID_MAIN_SubItem3    20012
#define ID_MAIN_ListViewMode    80004
#define ID_MAIN_Textview8    50008
#define ID_MAIN_Textview4    50004
#define ID_MAIN_Windowmode    110003
#define ID_MAIN_MusicListview    80009
#define ID_MAIN_ListWindow    110008
#define ID_MAIN_Pointer1    90001
#define ID_MAIN_SoneNameTextview    50021
#define ID_MAIN_ListButton    20017
#define ID_MAIN_Textview19    50020
#define ID_MAIN_Seekbar2    91003
#define ID_MAIN_VolWindow    110007
#define ID_MAIN_VolButton    20016
#define ID_MAIN_Textview7    50007
#define ID_MAIN_Seekbar1    91001
#define ID_MAIN_Button3    20004
#define ID_MAIN_Button2    20003
#define ID_MAIN_ButtonPlay    20002
#define ID_MAIN_Textview5    50005
#define ID_MAIN_WindowMusic    110002
#define ID_MAIN_Window1    110001
#define ID_MAIN_SubItem1    20001
#define ID_MAIN_Listview1    80001
/*TAG:Macro宏ID END*/

class mainActivity : public Activity, 
                     public ZKSeekBar::ISeekBarChangeListener, 
                     public ZKListView::IItemClickListener,
                     public ZKListView::AbsListAdapter,
                     public ZKSlideWindow::ISlideItemClickListener,
                     public EasyUIContext::ITouchListener,
                     public ZKEditText::ITextChangeListener,
                     public ZKVideoView::IVideoPlayerMessageListener
{
public:
    mainActivity();
    virtual ~mainActivity();

    /**
     * 注册定时器
     */
	void registerUserTimer(int id, int time);
	/**
	 * 取消定时器
	 */
	void unregisterUserTimer(int id);
	/**
	 * 重置定时器
	 */
	void resetUserTimer(int id, int time);

protected:
    /*TAG:PROTECTED_FUNCTION*/
    virtual const char* getAppName() const;
    virtual void onCreate();
    virtual void onClick(ZKBase *pBase);
    virtual void onResume();
    virtual void onPause();
    virtual void onIntent(const Intent *intentPtr);
    virtual bool onTimer(int id);

    virtual void onProgressChanged(ZKSeekBar *pSeekBar, int progress);

    virtual int getListItemCount(const ZKListView *pListView) const;
    virtual void obtainListItemData(ZKListView *pListView, ZKListView::ZKListItem *pListItem, int index);
    virtual void onItemClick(ZKListView *pListView, int index, int subItemIndex);

    virtual void onSlideItemClick(ZKSlideWindow *pSlideWindow, int index);

    virtual bool onTouchEvent(const MotionEvent &ev);

    virtual void onTextChanged(ZKTextView *pTextView, const string &text);

    void rigesterActivityTimer();

    virtual void onVideoPlayerMessage(ZKVideoView *pVideoView, int msg);
    void videoLoopPlayback(ZKVideoView *pVideoView, int msg, size_t callbackTabIndex);
    void startVideoLoopPlayback();
    void stopVideoLoopPlayback();
    bool parseVideoFileList(const char *pFileListPath, std::vector<string>& mediaFileList);
    int removeCharFromString(string& nString, char c);


private:
    /*TAG:PRIVATE_VARIABLE*/
    int mVideoLoopIndex;
    int mVideoLoopErrorCount;

};

#endif