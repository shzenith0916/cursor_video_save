import os
import threading
import subprocess
from datetime import datetime
from tkinter import filedialog, messagebox
from utils.utils import VideoUtils, show_custom_messagebox
from utils.extract.image_extractor import ImageUtils
from utils.event_system import event_system, Events
from utils.extract.video_extractor import VideoExtractor, ExtractConfig
from utils.extract.image_extractor import ImageExtractor
from utils.extract.audio_extractor import AudioExtractor


class ExtractionManager:
    """추출 작업 관리자"""

    def __init__(self, parent_frame, app, ffmpeg_manager=None):
        self.parent_frame = parent_frame
        self.app = app
        self.ffmpeg_manager = ffmpeg_manager

        # 작업 상태 플래그
        self._is_extracting = False
        self._is_image_extracting = False
        self._is_audio_extracting = False

        # 취소 이벤트 객체
        self.cancel_event = threading.Event()  # 취소 신호 전송 여부 확인

        # 추출 설정
        self.extract_config = ExtractConfig()

    def is_busy(self):
        """작업 중인지 확인"""
        return (self._is_extracting or
                self._is_image_extracting or
                self._is_audio_extracting)

    def _handle_extraction_error(self, extraction_type, error):
        """추출 준비 중 에러 처리"""
        messagebox.showerror(
            "오류", f"{extraction_type} 추출 준비 중 오류: {str(error)}")

# ======== 공개 API 메서드 ========

    def extract_video_segment(self, segment_info=None):
        """비디오 구간 추출"""
        try:
            # 중복 실행 방지
            if self._is_extracting:
                messagebox.showwarning(
                    "경고", "이미 비디오 추출 작업이 진행 중입니다.")
                return

            # 구간 정보 가져오기
            if not segment_info:
                segment_info = self._get_selected_segment_info()
                if not segment_info:
                    return

            # FFmpeg 확인
            if self.ffmpeg_manager and not self.ffmpeg_manager.require_ffmpeg_or_show_error(self.parent_frame, "비디오"):
                return

            # 입력 파일 찾기
            input_path = self._find_input_file(segment_info)
            if not input_path:
                return

            # 출력 파일 선택
            output_path = self._get_video_output_path(segment_info)
            if not output_path:
                return

            # 추출 시작
            self._start_video_extraction(input_path, output_path, segment_info)

        except Exception as e:
            self._handle_extraction_error("비디오", e)

    def extract_images(self, segment_info=None):
        """선택한 구간에서 이미지 추출"""
        try:
            # 중복 실행 방지
            if self._is_image_extracting:
                messagebox.showwarning(
                    "경고", "이미 이미지 추출 작업이 진행 중입니다.")
                return

            # 1. 선택한 구간 정보 가져오기
            if not segment_info:
                segment_info = self._get_selected_segment_info()
                if not segment_info:
                    return

            # 2. 입력 파일 찾기
            input_path = self._find_input_file(segment_info)
            if not input_path:
                return

            # 3.출력 폴더 설정
            output_folder = self._get_image_output_folder(
                input_path, segment_info)
            if not output_folder:
                return

            # 4. 이미지 추출 시작
            self._start_image_extraction(
                input_path, output_folder, segment_info)

        except Exception as e:
            self._handle_extraction_error("이미지", e)

    def extract_audio(self, segment_info=None):
        """오디오 추출"""
        try:
            # 중복 실행 방지
            if self._is_audio_extracting:
                messagebox.showwarning(
                    "경고", "이미 오디오 추출 작업이 진행 중입니다.")
                return

            # 구간 정보 가져오기
            if not segment_info:
                segment_info = self._get_selected_segment_info()
                if not segment_info:
                    return

            # FFmpeg 확인 (오디오 추출에는 필수)
            if self.ffmpeg_manager and not self.ffmpeg_manager.require_ffmpeg_or_show_error(self.parent_frame, "오디오"):
                return

            # 입력 파일 찾기
            input_path = self._find_input_file(segment_info)
            if not input_path:
                return

            # 출력 폴더 설정
            output_folder = self._get_audio_output_folder(
                input_path, segment_info)
            if not output_folder:
                return

            # 추출 시작
            self._start_audio_extraction(
                input_path, output_folder, segment_info)

        except Exception as e:
            self._handle_extraction_error("오디오", e)

# ====== 추출 관련 메서드 =======

    def _get_selected_segment_info(self):
        """선택된 구간 정보 가져오기"""
        if not hasattr(self.app, 'saved_segments') or not self.app.saved_segments:
            messagebox.showwarning(
                "경고", "추출할 구간이 없습니다.\n먼저 구간을 저장해주세요.")
            return None

        # UI에서 선택된 구간 우선 반환
        try:
            if hasattr(self.app, 'new_tab_instance') and \
               hasattr(self.app.new_tab_instance, 'segment_table') and \
               hasattr(self.app.new_tab_instance.segment_table, 'table'):
                tree = self.app.new_tab_instance.segment_table.table
                selected_items = tree.selection()
                if selected_items:
                    index = tree.index(selected_items[0])
                    if 0 <= index < len(self.app.saved_segments):
                        return self.app.saved_segments[index]
        except Exception:
            # 선택 정보 조회 실패 시 최신 구간으로 폴백
            pass

        # 선택이 없거나 에러 시 최신 구간 반환
        return self.app.saved_segments[-1]

    def _find_input_file(self, segment_info):
        """입력 파일 찾기"""
        input_path = VideoUtils.find_input_file(segment_info['file'], self.app)
        if not input_path or not os.path.exists(input_path):
            # 사용자가 직접 파일 선택
            response = messagebox.askyesno(
                "파일 없음",
                "원본 비디오 파일을 찾을 수 없습니다.\n직접 선택하시겠습니까?"
            )

            if response:
                input_path = filedialog.askopenfilename(
                    title="원본 비디오 파일 선택",
                    filetypes=VideoExtractor.get_supported_formats()
                )
                return input_path if input_path else None
            else:
                return None

        return input_path

    def _get_video_output_path(self, segment_info):
        """비디오 출력 파일 경로 설정"""
        default_filename = self.extract_config.generate_filename(segment_info)

        output_path = filedialog.asksaveasfilename(
            title="비디오 저장할 위치 선택",
            defaultextension=".mp4",
            filetypes=VideoExtractor.get_supported_formats(),
            initialfile=default_filename
        )

        return output_path if output_path else None

# ====== 이미지 추출 관련 메서드 =======

    def _get_image_output_folder(self, input_path, segment_info):
        """이미지 출력 폴더 설정"""
        folder_name = ImageUtils.generate_output_folder_name(
            input_path, segment_info['start'], segment_info['end'])

        default_path = VideoUtils.get_default_save_path()

        output_base_folder = filedialog.askdirectory(
            title="이미지 저장할 기본 폴더 선택",
            initialdir=default_path
        )
        if not output_base_folder:
            output_base_folder = default_path

        output_folder = os.path.join(output_base_folder, folder_name)

        # 폴더 생성
        if not self._create_output_folder(output_folder, folder_name):
            return None

        return output_folder

    def _get_audio_output_folder(self, input_path, segment_info):
        """오디오 출력 폴더 설정"""
        # 이미지와 동일한 방식 사용
        return self._get_image_output_folder(input_path, segment_info)

    def _create_output_folder(self, output_folder, folder_name):
        """출력 폴더 생성"""
        if os.path.exists(output_folder):
            response = messagebox.askyesno(
                "폴더 존재",
                f"폴더 '{folder_name}'이 이미 존재합니다.\n기존 폴더에 추가하시겠습니까?"
            )
            if not response:
                return False
        else:
            try:
                os.makedirs(output_folder, exist_ok=True)
            except Exception as e:
                messagebox.showwarning(
                    "오류", f"폴더 생성 실패: {str(e)}")
                return False
        return True

# ========= 스레드 연결 메서드 ==========

    def _start_video_extraction(self, input_path, output_path, segment_info):
        """비디오 추출 시작"""
        self._is_extracting = True
        self.cancel_event.clear()

        print(f"비디오 추출 시작: {segment_info['start']}~{segment_info['end']}초")

        # 비디오 추출 시작 (직접 메서드 호출로 변경됨)

        # 진행률 정보를 콜백으로 전달 (UI 업데이트는 new_tab.py에서)
        if hasattr(self, '_video_progress_callback'):
            self._video_progress_callback("비디오 추출 준비 중...")

        # 백그라운드 스레드에서 추출 실행
        threading.Thread(
            target=self._do_video_extraction,
            args=(input_path, output_path, segment_info),
            daemon=True
        ).start()

    def _start_image_extraction(self, input_path, output_folder, segment_info):
        """이미지 추출 시작"""
        self._is_image_extracting = True
        self.cancel_event.clear()  # 취소 신호 전송 False 값 전달

        print(f"이미지 추출 시작: {segment_info['start']}~{segment_info['end']}초")
        print(f"이미지 저장 폴더: {output_folder}")

        # 진행률 정보를 콜백으로 전달 (UI 업데이트는 new_tab.py에서)
        if hasattr(self, '_image_progress_callback'):
            # 이미지 추출 시작 시 초기 진행률 설정
            # progress=0, extracted_count=0, total_frames=0 (아직 추출 시작 전)
            self._image_progress_callback(0, 0, 0)

        # 백그라운드 스레드에서 추출 실행
        threading.Thread(
            target=self._do_image_extraction,
            args=(input_path, output_folder, segment_info),
            daemon=True
        ).start()

    def _start_audio_extraction(self, input_path, output_folder, segment_info):
        """오디오 추출 시작"""
        self._is_audio_extracting = True
        self.cancel_event.clear()

        print(f"오디오 추출 시작: {segment_info['start']}~{segment_info['end']}초")
        print(f"오디오 저장 폴더: {output_folder}")

        # 진행률 정보를 콜백으로 전달 (UI 업데이트는 new_tab.py에서)
        if hasattr(self, '_audio_progress_callback'):
            self._audio_progress_callback("오디오 추출 준비 중...")

        # 백그라운드 스레드에서 추출 실행
        threading.Thread(
            target=self._do_audio_extraction,
            args=(input_path, output_folder, segment_info),
            daemon=True
        ).start()

# ========= 실제 추출 메서드 ==========

    def _do_video_extraction(self, input_path, output_path, segment_info):
        """실제 비디오 추출 작업 (백그라운드)"""
        try:
            # # 취소 확인
            # if self.cancel_event.is_set():
            #     self._on_extraction_cancel()
            #     return

            # extract/video_extractor.py 의 VideoExtractor로 추출
            result = VideoExtractor.extract_segment(
                input_video_path=input_path,
                output_video_path=output_path,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=self._video_progress_callback,
                ffmpeg_executable=self._get_ffmpeg_executable(),
                cancel_event=self.cancel_event
            )

            # 결과 이벤트 발생
            self.parent_frame.after(
                0, lambda: self._emit_video_extraction_complete(result))

        except Exception as e:
            self.parent_frame.after(
                0, lambda err=e: self._handle_video_extraction_error(str(err)))

    def _do_image_extraction(self, input_path, output_folder, segment_info):
        """실제 이미지 추출 작업 (백그라운드)"""
        try:
            # 취소 확인
            if self.cancel_event.is_set():
                return  # 취소 시 단순히 종료

            # extract/ImageExtractor.py의 메서드를 사용하여 프레임 추출
            result = ImageExtractor.extract_frames_from_video(
                input_path=input_path,
                output_folder=output_folder,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                # 실제 추출 작업에서 진행률 콜백 호출함. 쓰레드에서 실행.
                progress_callback=self._image_progress_callback,
                cancel_event=self.cancel_event
            )

            # OpenCV가 실패하거나 0개 추출 시 FFmpeg 폴백 시도
            if (not result) or (result.get('extracted_count', 0) == 0):
                print("OpenCV 이미지 추출 결과가 0개입니다. FFmpeg 폴백(이미지 추출)을 시도합니다.")

                ff_result = ImageExtractor.extract_frames_with_ffmpeg(
                    input_path=input_path,
                    output_folder=output_folder,
                    start_time=segment_info['start'],
                    end_time=segment_info['end'],
                    ffmpeg_executable=self._get_ffmpeg_executable(),
                    cancel_event=self.cancel_event
                )
                if ff_result.get('success') and ff_result.get('extracted_count', 0) > 0:
                    # 폴백 성공 시 결과 변환하여 동일 경로로 전달
                    result = {
                        'extracted_count': ff_result.get('extracted_count', 0),
                        'total_frames': ff_result.get('extracted_count', 0),
                        'fps': 0,
                        'frame_skip': 0
                    }
                else:
                    # 폴백 실패 시 에러 이벤트
                    error_msg = ff_result.get('message', 'FFmpeg 폴백 실패')
                    self._handle_image_extraction_error(error_msg)
                    return

            # 취소되지 않았으면, 완료 이벤트 발행
            if not self.cancel_event.is_set():
                # 결과 이벤트 발생 (UI 업데이트는 new_tab.py에서 처리)
                self.parent_frame.after(
                    0, lambda: self._emit_image_extraction_complete(result, output_folder))

        except Exception as e:
            error_msg = f"이미지 추출 중 오류 발생: {str(e)}"
            self._handle_image_extraction_error(error_msg)

    def _do_audio_extraction(self, input_path, output_folder, segment_info):
        """실제 오디오 추출 작업 (백그라운드)"""
        try:
            # 취소 확인
            if self.cancel_event.is_set():
                return  # 취소 시 단순히 종료

            # AudioExtractor를 사용하여 오디오 추출
            base_filename = os.path.splitext(os.path.basename(input_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"{base_filename}_{timestamp}.mp3"
            output_path = os.path.join(output_folder, audio_filename)

            result = AudioExtractor.extract_audio_segment(
                input_video_path=input_path,
                output_audio_path=output_path,
                start_time=segment_info['start'],
                end_time=segment_info['end'],
                progress_callback=self._audio_progress_callback,
                audio_format='mp3',
                audio_quality='192k',
                ffmpeg_executable=self._get_ffmpeg_executable(),
                cancel_event=self.cancel_event
            )

            # 취소된 경우가 아니며 추출완료시, 완료 이벤트 발행
            if not self.cancel_event.is_set():
                # 결과 이벤트 발생
                self.parent_frame.after(
                    0, lambda: self._emit_audio_extraction_complete(result, output_folder))

        except Exception as e:
            self.parent_frame.after(
                0, lambda err=e: self._handle_audio_extraction_error(str(err)))

# ======== 진행률 콜백 메서드 =========

    def _video_progress_callback(self, message):
        """비디오 추출 진행률 콜백"""
        if not self.cancel_event.is_set():
            self.parent_frame.after(0, lambda: event_system.emit(
                Events.PROGRESS_UPDATE,
                progress=50,
                status=f"비디오 추출 중... {message}"))

    def _image_progress_callback(self, progress, extracted_count, total_frames):
        """이미지 추출 진행률 콜백
        Args:
            progress (int): 진행률 (0-100)
            extracted_count (int): 현재까지 추출된 이미지 개수
            total_frames (int): 전체 추출할 프레임 개수
        Note:
            ImageExtractor에서 호출되며, UI 업데이트를 위해 이벤트 시스템으로 전달
        """
        if not self.cancel_event.is_set():
            self.parent_frame.after(0, lambda: event_system.emit(
                Events.PROGRESS_UPDATE,
                progress=progress,
                extracted_count=extracted_count,
                total_frames=total_frames,
                status=f"이미지 {extracted_count}/{total_frames} 저장 중..."
            ))

    def _audio_progress_callback(self, message="오디오 추출 중..."):
        """오디오 추출 진행률 콜백"""
        if not self.cancel_event.is_set():
            self.parent_frame.after(0, lambda: event_system.emit(
                Events.PROGRESS_UPDATE,
                progress=50,
                status=message
            ))

# ========= 추출 시작 이벤트는 제거됨 - 직접 호출로 변경 =========

# ========= 추출 오류 이벤트 발행 관련 =========

    def _handle_video_extraction_error(self, error_msg):
        """비디오 추출 작업 중 오류가 발생했을때 호출되는 메서드 - 에러 이벤트 발행

        Note:
            비디오 추출은 취소 불가능하므로 취소 조건 없이 항상 오류 이벤트 발행
        """
        self._is_extracting = False

        self.parent_frame.after(0, lambda: event_system.emit(
            Events.VIDEO_EXTRACTION_ERROR,
            message=error_msg, progress=0, status="오류 발생", icon="⚠️"))

    def _handle_image_extraction_error(self, error_msg):
        """이미지 추출 작업 중 오류가 발생했을때 호출되는 메서드 - 에러 이벤트 발행"""
        self._is_image_extracting = False
        # 취소된 경우가 아니며 에러 발생시, 에러 이벤트 발행
        if not self.cancel_event.is_set():
            self.parent_frame.after(0, lambda: event_system.emit(
                Events.IMAGE_EXTRACTION_ERROR,
                message=error_msg, progress=0, status="오류 발생", icon="⚠️"))

    def _handle_audio_extraction_error(self, error_msg):
        """오디오 추출 작업 중 오류가 발생했을때 호출되는 메서드 - 에러 이벤트 발행"""
        self._is_audio_extracting = False

        # 취소된 경우가 아니며 에러 발생시, 에러 이벤트 발행
        if not self.cancel_event.is_set():
            self.parent_frame.after(0, lambda: event_system.emit(
                Events.AUDIO_EXTRACTION_ERROR, message=error_msg))

# ========= 추출 완료 이벤트 발행 관련 =========

    def _emit_video_extraction_complete(self, result):
        """비디오 추출 완료 이벤트 발행

        Args:
            result (dict): 추출 결과 정보 (output_path, success 등)
        Note:
            UI 업데이트는 new_tab.py의 _show_extraction_success에서 처리
        """
        self._is_extracting = False
        output_path = result.get('output_path', '')
        output_folder = os.path.dirname(output_path) if output_path else ''

        event_system.emit(
            Events.VIDEO_EXTRACTION_COMPLETE,
            extract_type="video",
            success=result.get('success', False),
            output_path=output_path,
            output_folder=output_folder
        )

    def _emit_image_extraction_complete(self, result, output_folder):
        """이미지 추출 완료 이벤트 발행

        Args:
            result (dict): 추출 결과 정보 (extracted_count, success 등)
            output_folder (str): 이미지 저장 폴더 경로
        Note:
            UI 업데이트는 new_tab.py의 _show_extraction_success에서 처리
        """
        self._is_image_extracting = False

        event_system.emit(
            Events.IMAGE_EXTRACTION_COMPLETE,
            extract_type="image",
            extracted_count=result['extracted_count'],
            output_folder=output_folder,  # 저장 위치 정보
            success=result.get('success', True)  # result에서 success 값 가져오기
        )

    def _emit_audio_extraction_complete(self, result, output_folder):
        """오디오 추출 완료 이벤트 발행

        Args:
            result (dict): 추출 결과 정보 (output_path, success 등)
            output_folder (str): 오디오 저장 폴더 경로
        Note:
            UI 업데이트는 new_tab.py의 _show_extraction_success에서 처리
        """
        self._is_audio_extracting = False
        output_path = result.get('output_path', '')
        output_folder = os.path.dirname(output_path) if output_path else ''

        event_system.emit(
            Events.AUDIO_EXTRACTION_COMPLETE,
            extract_type="audio",
            output_folder=output_folder,
            success=result.get('success', True)  # result에서 success 값 가져오기
        )

# ========= FFmpeg 관련 메서드 =========

    def _get_ffmpeg_executable(self):
        """FFmpeg 실행 경로 가져오기"""
        return (self.ffmpeg_manager.ffmpeg_path
                if self.ffmpeg_manager and self.ffmpeg_manager.ffmpeg_path else 'ffmpeg')

# ========= 추출 취소 요청청 메서드 =========

    def _cancel_all_extractions(self, **kwargs):
        """추출 취소 이벤트 발행 - 통합된 취소 처리"""
        try:
            # 상태 플래그 리셋
            self._is_image_extracting = False
            self._is_audio_extracting = False

            # 취소 이벤트 객체 설정
            self.cancel_event.set()
            # UI 업데이트는 new_tab.py에서 처리하므로 이벤트 발행 및 알림 제거
        except Exception as e:
            print(f"추출 취소 처리 중 오류: {str(e)}")
